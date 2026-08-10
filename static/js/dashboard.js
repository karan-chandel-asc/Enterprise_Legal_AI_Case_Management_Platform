// This page saves the shared create-case modal itself (to refresh dashboard
// data afterwards instead of navigating away), so tell global-case-modal.js
// not to also bind its own generic save handler to the same button.
window.CASE_MODAL_HANDLED = true;

document.addEventListener("DOMContentLoaded", () => {
  const goodMorning = qs("#good-morning");

  function renderKpis(kpis) {
    const kpiGrid = qs("#kpi-grid");
    kpiGrid.innerHTML = "";
    const resolutionRate = kpis.total_cases ? Math.round((kpis.closed_cases / kpis.total_cases) * 100) : 0;
    const kpiData = [
      { label: "Total Cases", value: kpis.total_cases, delta: `${kpis.total_cases} total cases` },
      { label: "Active Cases", value: kpis.active_cases, delta: `${kpis.active_cases} active cases` },
      { label: "Closed Cases", value: kpis.closed_cases, delta: `${resolutionRate}% resolution rate` },
      { label: "Next Hearings", value: kpis.hearings_this_week, delta: `${kpis.hearings_this_week} scheduled ahead this week` },
 
    ];
    kpiData.forEach((k) => {
      kpiGrid.appendChild(el("div", { class: "card kpi-card" }, [
        el("div", { class: "l" }, [k.label]),
        el("div", { class: "v" }, [String(k.value)]),
        el("div", { class: "d up" }, [k.delta]),
      ]));
    });
  }

  function renderRecentCases(cases) {
    const tbody = qs("#recent-cases-body");
    tbody.innerHTML = "";
    if (!cases.length) {
      tbody.appendChild(el("tr", {}, [
        el("td", { colspan: "4", class: "text-sm text-muted", style: "padding:18px 4px;" }, ["No cases yet — create your first case to see it here."]),
      ]));
      return;
    }
    cases.forEach((c) => {
      tbody.appendChild(el("tr", { onclick: () => (window.location.href = `/cases/${c.id}/`) }, [
        el("td", {}, [el("span", { class: "cell-primary" }, [c.case_title])]),
        el("td", { class: "cell-muted" }, [c.court_name ? c.court_name.split(",")[0] : "—"]),
        el("td", { html: statusBadge(c.case_status) }),
        el("td", { class: "cell-muted" }, [c.hearing_date || "—"]),
      ]));
    });
  }

  function renderUpcomingHearings(hearings) {
    const box = qs("#upcoming-hearings");
    box.innerHTML = "";
    if (!hearings.length) {
      box.appendChild(el("div", { class: "text-sm text-muted", style: "padding:12px 4px;" }, ["No upcoming hearings scheduled."]));
      return;
    }
    hearings.forEach((h) => {
      const days = daysUntil(h.hearing_date);
      box.appendChild(el("div", { class: "list-row", onclick: () => (window.location.href = `/cases/${h.case_id}/`) }, [
        el("div", { class: "main" }, [
          el("b", {}, [h.case_title]),
          el("span", {}, [`${formatDateLong(h.hearing_date)} · ${h.hearing_time}`]),
        ]),
        el("div", { class: "side" }, [
          el("span", { class: `badge ${days <= 2 ? "badge-danger" : "badge-neutral"}` }, [days === 0 ? "Today" : `${days}d`]),
        ]),
      ]));
    });
  }

  function renderAiWidgets(aiActivity, recentAiChats) {
    const chart = qs("#ai-chart");
    const chatsBox = qs("#recent-ai-chats");
    const meta = qs("#ai-total-meta");
    chart.innerHTML = "";
    chatsBox.innerHTML = "";

    const series = (aiActivity && aiActivity.series) || [];
    const total = (aiActivity && aiActivity.total_queries) || 0;
    const days = (aiActivity && aiActivity.days) || 14;
    meta.textContent = `${total} quer${total === 1 ? "y" : "ies"} · last ${days} days`;

    if (!series.length || total === 0) {
      // Flat empty bars so the chart area still has structure.
      for (let i = 0; i < days; i++) {
        chart.appendChild(el("i", { style: "height:8%", class: "" }));
      }
    } else {
      const max = Math.max(...series.map((d) => d.count), 1);
      series.forEach((d, i) => {
        const pct = Math.max(8, Math.round((d.count / max) * 100));
        chart.appendChild(el("i", {
          style: `height:${pct}%`,
          class: i >= series.length - 5 && d.count > 0 ? "hi" : "",
          title: `${d.date}: ${d.count}`,
        }));
      });
    }

    if (!recentAiChats || !recentAiChats.length) {
      chatsBox.appendChild(el("div", {
        class: "text-sm text-muted",
        style: "padding:12px 4px;",
      }, ["No recent AI chats yet — open a case and ask the assistant."]));
      return;
    }

    recentAiChats.forEach((c) => {
      chatsBox.appendChild(el("div", {
        class: "list-row",
        onclick: () => (window.location.href = `/cases/${c.case_id}/`),
      }, [
        el("div", { class: "main" }, [
          el("b", {}, [`\u201c${c.query}\u201d`]),
          el("span", {}, [c.case_title || "—"]),
        ]),
        el("div", { class: "side" }, [c.time || ""]),
      ]));
    });
  }

  async function loadDashboard() {
    try {
      const res = await fetch(window.DASHBOARD_API_URL, { headers: { Accept: "application/json" } });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not load dashboard", "error");
        return;
      }
      const { kpis, recent_cases, upcoming_hearings, ai_activity, recent_ai_chats } = result.data;
      const fullName = result.data.user.full_name;
      const formattedName = fullName
          .split(" ")
          .map(name => name.charAt(0).toUpperCase() + name.slice(1))
          .join(" ");

      goodMorning.textContent = `Good morning, ${formattedName}`;
      renderKpis(kpis);
      renderRecentCases(recent_cases);
      renderUpcomingHearings(upcoming_hearings);
      renderAiWidgets(ai_activity, recent_ai_chats);
    } catch (err) {
      toast("Could not load dashboard. Please refresh.", "error");
    }
  }

  qs("#dash-new-case-btn").addEventListener("click", () => window.openCreateCaseModal());

  qs("#case-save-btn").addEventListener("click", async () => {
    const title = qs("#f-title").value.trim();
    if (!title) { toast("Case title is required", "error"); return; }

    const payload = {
      case_id: qs("#f-number").value.trim(),
      case_title: title,
      case_type: qs("#f-type").value,
      case_status: qs("#f-status").value,
      client_name: qs("#f-client").value,
      opposing_party_name: qs("#f-opposite").value,
      court_name: qs("#f-court").value,
      hearing_date: qs("#f-hearing").value,
      case_description: qs("#f-desc").value,
    };

    const saveBtn = qs("#case-save-btn");
    saveBtn.disabled = true;
    try {
      const res = await fetch(window.CASES_CREATE_API_URL, {
        method: "POST",
        headers: jsonHeaders(),
        body: JSON.stringify(payload),
      });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not create case", "error");
        return;
      }
      toast("Case created", "success");
      closeModal("case-modal");
      loadDashboard();
    } catch (err) {
      toast("Could not save case. Please try again.", "error");
    } finally {
      saveBtn.disabled = false;
    }
  });

  loadDashboard();
});
