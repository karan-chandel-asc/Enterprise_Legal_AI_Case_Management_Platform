from collections import Counter, defaultdict
from datetime import timedelta
from urllib.parse import urlparse
from urllib.request import urlopen
import json
import uuid

from django.conf import settings
from django.utils import timezone

from Enterprise_Legal_AI_Case_Management_Platform.logger import logger
from analytics.models import AnalyticsEvent

# Frontend may only emit these event names — keeps the ingest surface tight.
ALLOWED_FRONTEND_EVENTS = {
    "page.viewed",
    "cta.clicked",
}

VISITOR_COOKIE = "lexora_vid"

# Human labels used when telling the visitor's story in email.
STEP_LABELS = {
    "page.viewed": "Opened a page",
    "cta.clicked": "Clicked a button",
    "user.signed_up": "Signed up",
    "user.signup_failed": "Tried to sign up (failed)",
    "user.logged_in": "Logged in",
    "user.login_failed": "Tried to login (failed)",
    "user.login_mfa_required": "Reached MFA step",
    "user.logged_out": "Logged out",
    "case.created": "Created a case",
    "document.uploaded": "Uploaded a document",
    "embedding.completed": "Document indexing completed",
    "embedding.failed": "Document indexing failed",
    "chat.message_sent": "Ran AI chat",
    "chat.message_failed": "AI chat failed",
    "search.queried": "Used semantic search",
}

INTEREST_WEIGHTS = {
    "user.signed_up": 5,
    "user.logged_in": 4,
    "case.created": 5,
    "document.uploaded": 4,
    "chat.message_sent": 5,
    "search.queried": 3,
    "page.viewed": 1,
    "cta.clicked": 1,
}


def _client_ip(request) -> str | None:
    if request is None:
        return None
    forwarded = (request.META.get("HTTP_X_FORWARDED_FOR") or "").split(",")[0].strip()
    ip = forwarded or request.META.get("REMOTE_ADDR") or ""
    return ip or None


def _host_from_referrer(referrer: str) -> str:
    if not referrer:
        return "direct / unknown"
    try:
        host = urlparse(referrer).netloc or referrer
        return host.lower().removeprefix("www.")[:120]
    except Exception:
        return referrer[:120]


class AnalyticsService:
    @staticmethod
    def track(
        event_name: str,
        *,
        user=None,
        email: str = "",
        status: str = "info",
        page: str = "",
        source: str = "backend",
        message: str = "",
        metadata: dict | None = None,
        request=None,
        visitor_id: str = "",
        referrer: str = "",
    ) -> AnalyticsEvent | None:
        """Best-effort event write — never raises into the caller's request path."""
        try:
            if request is not None and user is None and getattr(request, "user", None):
                if request.user.is_authenticated:
                    user = request.user

            resolved_email = (email or "").strip().lower()
            if not resolved_email and user is not None:
                resolved_email = (getattr(user, "email", "") or "").strip().lower()

            meta = dict(metadata or {})
            vid = (visitor_id or meta.pop("visitor_id", "") or "").strip()
            ref = (referrer or meta.pop("referrer", "") or "").strip()

            if request is not None:
                meta.setdefault("path", request.path)
                ua = request.META.get("HTTP_USER_AGENT", "")
                if ua:
                    meta.setdefault("user_agent", ua[:180])
                if not vid:
                    vid = (request.COOKIES.get(VISITOR_COOKIE) or "").strip()
                if not ref:
                    ref = (request.META.get("HTTP_REFERER") or "").strip()

            if not vid and request is not None and hasattr(request, "session"):
                vid = request.session.get("analytics_visitor_id") or ""
                if not vid:
                    vid = uuid.uuid4().hex
                    request.session["analytics_visitor_id"] = vid

            ip = _client_ip(request)
            location = ""
            # Prefer client-provided location only if already present; geo is
            # resolved in bulk when building the interest email.
            if meta.get("location"):
                location = str(meta.pop("location"))[:120]

            return AnalyticsEvent.objects.create(
                user=user if user is not None and getattr(user, "is_authenticated", True) else None,
                email=resolved_email,
                visitor_id=vid[:64],
                referrer=ref[:500],
                ip_address=ip,
                location=location,
                event_name=event_name[:80],
                status=status if status in {"started", "succeeded", "failed", "info"} else "info",
                page=(page or "")[:120],
                source=(source or "backend")[:40],
                message=(message or "")[:255],
                metadata=meta,
            )
        except Exception as e:
            logger.error(f"[Analytics] failed to track {event_name}: {e}")
            return None

    @classmethod
    def resolve_locations(cls, events) -> dict[str, str]:
        """Map unique public IPs → 'City, Country' using a free lookup (best-effort)."""
        cache: dict[str, str] = {}
        ips = {e.ip_address for e in events if e.ip_address}
        for ip in ips:
            if not ip or ip.startswith("127.") or ip.startswith("192.168.") or ip == "::1":
                cache[ip] = "Local / private network"
                continue
            try:
                with urlopen(f"http://ip-api.com/json/{ip}?fields=status,city,country", timeout=2) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if data.get("status") == "success":
                    city = data.get("city") or ""
                    country = data.get("country") or ""
                    label = ", ".join(p for p in (city, country) if p) or "Unknown"
                else:
                    label = "Unknown"
                cache[ip] = label[:120]
            except Exception:
                cache[ip] = "Unknown"
        return cache

    @classmethod
    def _journey_key(cls, event: AnalyticsEvent) -> str:
        if event.email:
            return f"email:{event.email}"
        if event.visitor_id:
            return f"vid:{event.visitor_id}"
        if event.ip_address:
            return f"ip:{event.ip_address}"
        return f"anon:{event.id}"

    @classmethod
    def _interest_score(cls, event_names: list[str]) -> int:
        return sum(INTEREST_WEIGHTS.get(name, 0) for name in event_names)

    @classmethod
    def build_journeys(cls, events, geo_map: dict[str, str]) -> list[dict]:
        buckets: dict[str, list] = defaultdict(list)
        for event in events:
            buckets[cls._journey_key(event)].append(event)

        journeys = []
        for key, rows in buckets.items():
            rows = sorted(rows, key=lambda e: e.created_at)
            first, last = rows[0], rows[-1]
            names = [e.event_name for e in rows]
            pages = [e.page for e in rows if e.page]
            email = next((e.email for e in rows if e.email), "")
            location = next((e.location for e in rows if e.location), "")
            if not location and first.ip_address:
                location = geo_map.get(first.ip_address, "")
            referrer = next((e.referrer for e in rows if e.referrer), "")
            came_from = _host_from_referrer(referrer)
            utm = {}
            for e in rows:
                meta = e.metadata or {}
                for k in ("utm_source", "utm_medium", "utm_campaign", "utm_content"):
                    if meta.get(k) and k not in utm:
                        utm[k] = str(meta[k])[:80]

            steps = []
            seen_step = set()
            for e in rows:
                label = STEP_LABELS.get(e.event_name, e.event_name)
                detail = ""
                if e.event_name == "page.viewed" and e.page:
                    detail = e.page
                elif e.event_name == "cta.clicked":
                    detail = (e.metadata or {}).get("cta", "")
                elif e.event_name == "case.created":
                    detail = f"case_id={(e.metadata or {}).get('case_id', '')}"
                step_key = f"{label}|{detail}"
                if step_key in seen_step and e.event_name in {"page.viewed", "cta.clicked"}:
                    continue
                seen_step.add(step_key)
                ts = timezone.localtime(e.created_at).strftime("%H:%M")
                steps.append(f"{ts} — {label}" + (f" ({detail})" if detail else ""))

            score = cls._interest_score(names)
            journeys.append(
                {
                    "key": key,
                    "email": email or "anonymous visitor",
                    "location": location or "Unknown location",
                    "came_from": came_from,
                    "utm": utm,
                    "ip": first.ip_address or "",
                    "first_seen": first.created_at,
                    "last_seen": last.created_at,
                    "event_count": len(rows),
                    "pages": list(dict.fromkeys(pages))[:8],
                    "signed_up": "user.signed_up" in names,
                    "logged_in": "user.logged_in" in names,
                    "created_case": "case.created" in names,
                    "uploaded_doc": "document.uploaded" in names,
                    "used_chat": "chat.message_sent" in names,
                    "used_search": "search.queried" in names,
                    "opened_dashboard": any(p == "dashboard" for p in pages),
                    "steps": steps[:25],
                    "score": score,
                }
            )

        journeys.sort(key=lambda j: (-j["score"], -j["event_count"], j["first_seen"]))
        return journeys

    @classmethod
    def build_daily_digest(cls, hours: int = 24) -> dict:
        since = timezone.now() - timedelta(hours=hours)
        until = timezone.now()
        qs = list(AnalyticsEvent.objects.filter(created_at__gte=since, created_at__lte=until).order_by("created_at"))

        # Fill missing location labels once per IP, then persist for the email.
        geo_map = cls.resolve_locations([e for e in qs if not e.location])
        for event in qs:
            if not event.location and event.ip_address and event.ip_address in geo_map:
                event.location = geo_map[event.ip_address]
                AnalyticsEvent.objects.filter(pk=event.pk).update(location=event.location)

        journeys = cls.build_journeys(qs, geo_map)
        by_event = Counter(e.event_name for e in qs)

        interested = [
            j
            for j in journeys
            if j["signed_up"]
            or j["logged_in"]
            or j["created_case"]
            or j["used_chat"]
            or j["used_search"]
            or j["score"] >= 3
        ]

        return {
            "since": since,
            "until": until,
            "hours": hours,
            "total_events": len(qs),
            "unique_visitors": len(journeys),
            "interested_visitors": len(interested),
            "signups": by_event.get("user.signed_up", 0),
            "logins": by_event.get("user.logged_in", 0),
            "cases_created": by_event.get("case.created", 0),
            "documents_uploaded": by_event.get("document.uploaded", 0),
            "chat_succeeded": by_event.get("chat.message_sent", 0),
            "searches": by_event.get("search.queried", 0),
            "page_views": by_event.get("page.viewed", 0),
            "journeys": journeys[:20],
            "interested": interested[:15],
            "recipient": getattr(settings, "ANALYTICS_DIGEST_EMAIL", "") or settings.DEFAULT_FROM_EMAIL,
        }

    @classmethod
    def delete_events_in_window(cls, since, until) -> int:
        """Remove events that were included in a successfully emailed digest."""
        deleted, _ = AnalyticsEvent.objects.filter(
            created_at__gte=since,
            created_at__lte=until,
        ).delete()
        return deleted

    @classmethod
    def format_digest_email(cls, digest: dict) -> tuple[str, str]:
        since = digest["since"].strftime("%Y-%m-%d %H:%M UTC")
        until = digest["until"].strftime("%Y-%m-%d %H:%M UTC")
        n = digest["unique_visitors"]
        hot = digest["interested_visitors"]
        subject = (
            f"[Lexora Demo] {hot} interested visitor(s) — {n} total checked your project"
            if n
            else f"[Lexora Demo] No visitors in the last {digest['hours']}h"
        )

        if not digest["journeys"]:
            body = f"""Lexora demo interest report
Window: {since} → {until}

Nobody visited your project in this window yet.

Tip: share your demo link on Upwork with ?utm_source=upwork so you can see where leads come from.

— Lexora interest tracker
"""
            return subject, body

        journey_blocks = []
        for i, j in enumerate(digest["journeys"], start=1):
            flags = []
            if j["signed_up"]:
                flags.append("signed up")
            if j["logged_in"]:
                flags.append("logged in")
            if j["opened_dashboard"]:
                flags.append("opened dashboard")
            if j["created_case"]:
                flags.append("created case")
            if j["uploaded_doc"]:
                flags.append("uploaded document")
            if j["used_search"]:
                flags.append("used search")
            if j["used_chat"]:
                flags.append("ran AI chat")
            flag_line = " -> ".join(flags) if flags else "browsed only"

            utm_bits = ", ".join(f"{k}={v}" for k, v in j["utm"].items()) or "none"
            steps = "\n".join(f"    {s}" for s in j["steps"]) or "    (no steps)"
            first = timezone.localtime(j["first_seen"]).strftime("%Y-%m-%d %H:%M")
            last = timezone.localtime(j["last_seen"]).strftime("%H:%M")

            journey_blocks.append(
                f"""#{i} {j['email']}
  Location:   {j['location']}
  Came from:  {j['came_from']}
  UTM:        {utm_bits}
  Interest:   {flag_line}
  Score:      {j['score']}  |  events: {j['event_count']}  |  {first} -> {last}
  Journey:
{steps}"""
            )

        body = f"""Lexora demo interest report (Upwork / portfolio)
Window: {since} → {until}

Someone checked your project? Here's who and what they tried.

=== Snapshot ===
Unique visitors:     {digest['unique_visitors']}
Interested visitors: {digest['interested_visitors']}
Signups:             {digest['signups']}
Logins:              {digest['logins']}
Cases created:       {digest['cases_created']}
Documents uploaded:  {digest['documents_uploaded']}
AI chats:            {digest['chat_succeeded']}
Searches:            {digest['searches']}
Page views:          {digest['page_views']}

=== Visitor journeys (source -> location -> actions) ===
{chr(10).join(journey_blocks)}

— Lexora interest tracker
After this email, these events are cleared from the database.
"""
        return subject, body
