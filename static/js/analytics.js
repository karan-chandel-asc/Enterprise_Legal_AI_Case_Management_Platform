/**
 * Demo interest tracker — page views + CTA clicks, with a stable visitor id
 * so we can email a journey: came from → location → login → cases → chat.
 */
(function () {
  const ENDPOINT = window.ANALYTICS_EVENTS_API_URL;
  if (!ENDPOINT) return;

  const VID_KEY = "lexora_vid";

  function csrfToken() {
    if (typeof getCookie === "function") return getCookie("csrftoken");
    const el = document.querySelector("[name=csrfmiddlewaretoken]");
    if (el && el.value) return el.value;
    const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function uuid() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID().replace(/-/g, "");
    return "v" + Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
  }

  function getVisitorId() {
    try {
      let id = localStorage.getItem(VID_KEY);
      if (!id) {
        id = uuid();
        localStorage.setItem(VID_KEY, id);
      }
      document.cookie = `${VID_KEY}=${id};path=/;max-age=31536000;SameSite=Lax`;
      return id;
    } catch (_) {
      return uuid();
    }
  }

  function utmParams() {
    const out = {};
    try {
      const params = new URLSearchParams(location.search);
      ["utm_source", "utm_medium", "utm_campaign", "utm_content"].forEach((k) => {
        const v = params.get(k);
        if (v) out[k] = v.slice(0, 80);
      });
    } catch (_) {}
    return out;
  }

  function track(eventName, payload) {
    const meta = Object.assign({}, utmParams(), (payload && payload.metadata) || {});
    const body = {
      event_name: eventName,
      status: (payload && payload.status) || "info",
      page: (payload && payload.page) || document.body?.dataset?.page || "",
      message: (payload && payload.message) || "",
      visitor_id: getVisitorId(),
      referrer: document.referrer || "",
      metadata: meta,
    };
    try {
      fetch(ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken(),
        },
        credentials: "same-origin",
        body: JSON.stringify(body),
        keepalive: true,
      }).catch(() => {});
    } catch (_) {}
  }

  window.trackAnalytics = track;

  track("page.viewed", {
    page: document.body?.dataset?.page || location.pathname,
    metadata: { path: location.pathname, title: document.title },
  });

  document.addEventListener(
    "click",
    (e) => {
      const target = e.target.closest("[data-analytics-cta]");
      if (!target) return;
      const cta = target.getAttribute("data-analytics-cta") || "unknown";
      track("cta.clicked", {
        page: document.body?.dataset?.page || location.pathname,
        metadata: {
          cta,
          href: target.getAttribute("href") || "",
          id: target.id || "",
        },
      });
    },
    true
  );
})();
