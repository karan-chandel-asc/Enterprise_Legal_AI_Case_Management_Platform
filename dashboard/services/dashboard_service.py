from datetime import date, timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from Enterprise_Legal_AI_Case_Management_Platform.logger import logger
from case_management.models import Case, Hearing
from chatbot.models import ChatMessage


class DashboardService:
    def get_kpis(self, user):
        try:
            cases = Case.objects.filter(user=user)
            total = cases.count()
            active = cases.filter(case_status='active').count()
            closed = cases.filter(case_status='closed').count()

            today = date.today()
            # "Hearing" is no longer a case-level status — a case counts as
            # awaiting a hearing if it has any upcoming (not completed/
            # cancelled) row in the Hearing model.
            cases_awaiting_hearing = Hearing.objects.filter(
                case__user=user,
                hearing_date__gte=today,
            ).exclude(status__in=['completed', 'cancelled']).values('case_id').distinct().count()
            hearings_this_week = Hearing.objects.filter(
                case__user=user,
                hearing_date__gte=today,
                hearing_date__lte=today + timedelta(days=7),
            ).count()

            return {
                "total_cases": total,
                "active_cases": active,
                "closed_cases": closed,
                "hearing_cases": cases_awaiting_hearing,
                "hearings_this_week": hearings_this_week,
            }
        except Exception as e:
            logger.error(f"Error getting dashboard KPIs: {e}")
            raise

    def get_recent_cases(self, user, limit=5):
        try:
            return Case.objects.filter(user=user).order_by('-case_created_at')[:limit]
        except Exception as e:
            logger.error(f"Error getting recent cases: {e}")
            raise

    def get_upcoming_hearings(self, user, limit=4):
        try:
            return Hearing.objects.select_related('case').filter(
                case__user=user, hearing_date__gte=date.today()
            ).order_by('hearing_date', 'hearing_time')[:limit]
        except Exception as e:
            logger.error(f"Error getting upcoming hearings: {e}")
            raise

    def get_ai_activity(self, user, days=14):
        """Daily user-query counts for the AI activity chart (last N days)."""
        try:
            now = timezone.now()
            start = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
            rows = (
                ChatMessage.objects.filter(
                    case__user=user,
                    role="user",
                    created_at__gte=start,
                )
                .annotate(day=TruncDate("created_at"))
                .values("day")
                .annotate(count=Count("id"))
            )
            by_day = {row["day"]: row["count"] for row in rows}

            series = []
            total = 0
            for offset in range(days):
                day = (start + timedelta(days=offset)).date()
                count = by_day.get(day, 0)
                total += count
                series.append({"date": day.isoformat(), "count": count})

            return {"days": days, "total_queries": total, "series": series}
        except Exception as e:
            logger.error(f"Error getting AI activity: {e}")
            raise

    def get_recent_ai_chats(self, user, limit=5):
        """Most recent user questions across the lawyer's cases."""
        try:
            return (
                ChatMessage.objects.select_related("case")
                .filter(case__user=user, role="user")
                .order_by("-created_at")[:limit]
            )
        except Exception as e:
            logger.error(f"Error getting recent AI chats: {e}")
            raise
