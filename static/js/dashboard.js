document.addEventListener("DOMContentLoaded", () => {
  const { kpis, cases, hearings, recentAiChats } = DEMO;

  // KPI cards
  const kpiGrid = qs("#kpi-grid");
  const kpiData = [
    { label: "Total Cases", value: kpis.totalCases, delta: "+3 this month", up: true },
    { label: "Active Cases", value: kpis.activeCases, delta: "+2 this month", up: true },
    { label: "Closed Cases", value: kpis.closedCases, delta: `${Math.round((kpis.closedCases / kpis.totalCases) * 100)}% resolution rate`, up: true },
    { label: "AI Chats This Week", value: kpis.aiChatsWeek, delta: `+${kpis.aiChatsDelta}% vs last week`, up: true },
  ];
  kpiData.forEach((k) => {
    kpiGrid.appendChild(el("div", { class: "card kpi-card" }, [
      el("div", { class: "l" }, [k.label]),
      el("div", { class: "v" }, [String(k.value)]),
      el("div", { class: `d ${k.up ? "up" : "down"}` }, [
        (() => { const s = document.createElement("span"); s.innerHTML = k.up
          ? '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><polyline points="18 15 12 9 6 15"/></svg>'
          : '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><polyline points="6 9 12 15 18 9"/></svg>';
          return s; })(),
        k.delta,
      ]),
    ]));
  });

  // AI activity chart (14 fake days, weighted toward recent)
  const chart = qs("#ai-chart");
  const heights = [22, 35, 30, 48, 40, 55, 45, 62, 58, 74, 66, 80, 70, 92];
  heights.forEach((h, i) => {
    chart.appendChild(el("i", { style: `height:${h}%`, class: i >= heights.length - 5 ? "hi" : "" }));
  });
  qs("#ai-total-meta").textContent = `${kpis.aiChatsWeek} queries · last 14 days`;

  // Recent cases table
  const tbody = qs("#recent-cases-body");
  cases.slice(0, 5).forEach((c) => {
    const tr = el("tr", { onclick: () => (window.location.href = `/cases/${c.id}/`) }, [
      el("td", {}, [el("span", { class: "cell-primary" }, [c.title])]),
      el("td", { class: "cell-muted" }, [c.court.split(",")[0]]),
      el("td", { html: statusBadge(c.status) }),
      el("td", { class: "cell-muted" }, [c.hearingDate ? formatDateLong(c.hearingDate) : "—"]),
    ]);
    tbody.appendChild(tr);
  });

  // Upcoming hearings
  const hearingsBox = qs("#upcoming-hearings");
  hearings.slice(0, 4).forEach((h) => {
    const days = daysUntil(h.date);
    hearingsBox.appendChild(el("div", { class: "list-row", onclick: () => (window.location.href = `/cases/${h.caseId}/`) }, [
      el("div", { class: "main" }, [
        el("b", {}, [h.caseTitle]),
        el("span", {}, [`${formatDateLong(h.date)} · ${h.time}`]),
      ]),
      el("div", { class: "side" }, [
        el("span", { class: `badge ${days <= 2 ? "badge-danger" : "badge-neutral"}` }, [days === 0 ? "Today" : `${days}d`]),
      ]),
    ]));
  });

  // Recent AI chats
  const chatsBox = qs("#recent-ai-chats");
  recentAiChats.forEach((c) => {
    chatsBox.appendChild(el("div", { class: "list-row" }, [
      el("div", { class: "main" }, [
        el("b", {}, [`“${c.query}”`]),
        el("span", {}, [c.case]),
      ]),
      el("div", { class: "side" }, [c.time]),
    ]));
  });
});
