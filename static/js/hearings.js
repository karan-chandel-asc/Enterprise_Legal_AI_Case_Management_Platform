document.addEventListener("DOMContentLoaded", () => {
  let hearings = [];
  let cases = [];
  const now = new Date();
  let viewYear = now.getFullYear(), viewMonth = now.getMonth();
  const today = now;
  const MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

  function mapHearing(h) {
    return {
      id: h.id,
      caseId: h.case_id,
      caseTitle: h.case_title,
      caseNumber: h.case_number,
      date: h.hearing_date,
      time: h.hearing_time || "Time TBD",
      court: h.court_name || "—",
      judge: h.judge_name || "—",
      status: h.status,
      notes: h.notes,
    };
  }

  function dayCell(num, muted, iso, isToday) {
    const cell = el("div", { class: `cal-day ${muted ? "muted" : ""} ${isToday ? "today" : ""}` });
    cell.appendChild(el("div", { class: "num" }, [String(num)]));
    if (iso) {
      hearings.filter((h) => h.date === iso).forEach((h) => {
        cell.appendChild(el("div", { class: `cal-event ${h.status === "urgent" ? "urgent" : ""}`, onclick: (e) => { e.stopPropagation(); openHearing(h); } }, [h.caseTitle]));
      });
    }
    return cell;
  }

  function renderCalendar() {
    const grid = qs("#cal-grid");
    grid.innerHTML = "";
    qs("#cal-label").textContent = `${MONTH_NAMES[viewMonth]} ${viewYear}`;
    ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].forEach((d) => grid.appendChild(el("div", { class: "cal-dow" }, [d])));

    const firstDay = new Date(viewYear, viewMonth, 1).getDay();
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
    const daysInPrevMonth = new Date(viewYear, viewMonth, 0).getDate();

    for (let i = firstDay - 1; i >= 0; i--) grid.appendChild(dayCell(daysInPrevMonth - i, true, null));
    for (let d = 1; d <= daysInMonth; d++) {
      const iso = `${viewYear}-${String(viewMonth + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      const isToday = viewYear === today.getFullYear() && viewMonth === today.getMonth() && d === today.getDate();
      grid.appendChild(dayCell(d, false, iso, isToday));
    }
    const trailing = (7 - ((firstDay + daysInMonth) % 7)) % 7;
    for (let i = 1; i <= trailing; i++) grid.appendChild(dayCell(i, true, null));
  }

  function renderList() {
    const box = qs("#hearing-list");
    box.innerHTML = "";
    if (!hearings.length) {
      box.appendChild(el("div", { class: "text-sm text-muted", style: "padding:16px;" }, ["No hearings scheduled this month."]));
      return;
    }
    [...hearings].sort((a, b) => a.date.localeCompare(b.date)).forEach((h) => {
      const { day, month } = formatDateShort(h.date);
      box.appendChild(el("div", { class: "hearing-list-item", onclick: () => openHearing(h) }, [
        el("div", { class: "hearing-date-block" }, [el("div", { class: "d" }, [String(day)]), el("div", { class: "m" }, [month])]),
        el("div", { class: "flex-1" }, [
          el("b", { style: "display:block;font-size:13px;" }, [h.caseTitle]),
          el("span", { class: "text-sm text-muted" }, [`${h.time} · ${h.court.split(",")[0]}`]),
          el("div", { style: "margin-top:4px;", html: statusBadge(h.status) }),
        ]),
      ]));
    });
  }

  function updateSubtitle() {
    const caseCount = new Set(hearings.map((h) => h.caseId)).size;
    qs("#hearings-subtitle").textContent = `${hearings.length} hearing${hearings.length === 1 ? "" : "s"} across ${caseCount} case${caseCount === 1 ? "" : "s"} this month.`;
  }

  function openHearing(h) {
    qs("#ho-case-tag").textContent = (h.caseNumber || "").toUpperCase();
    qs("#ho-title").textContent = h.caseTitle;
    qs("#ho-status").innerHTML = statusBadge(h.status);
    qs("#ho-datetime").textContent = `${formatDateLong(h.date)} · ${h.time}`;
    qs("#ho-court").textContent = h.court;
    qs("#ho-judge").textContent = h.judge;
    qs("#ho-notes").textContent = h.notes || "No notes added.";
    qs("#ho-open-case").setAttribute("href", `/cases/${h.caseId}/`);
    qs("#hearing-slideover").classList.add("open");
  }

  async function loadHearings() {
    try {
      const params = new URLSearchParams({ month: viewMonth + 1, year: viewYear });
      const res = await fetch(`${window.HEARINGS_API_URL}?${params.toString()}`, { headers: { Accept: "application/json" } });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not load hearings", "error");
        return;
      }
      hearings = (result.data || []).map(mapHearing);
      renderCalendar();
      renderList();
      updateSubtitle();
    } catch (err) {
      toast("Could not load hearings. Please refresh.", "error");
    }
  }

  async function loadCases() {
    try {
      const res = await fetch(`${window.CASES_LIST_API_URL}?page_size=100`, { headers: { Accept: "application/json" } });
      const result = await res.json();
      if (res.ok && result.success) {
        cases = (result.data && result.data.cases) || [];
      }
    } catch (err) {
      // Non-critical — the schedule modal will just show an empty case list.
    }
  }

  qs("#cal-prev").addEventListener("click", () => { viewMonth--; if (viewMonth < 0) { viewMonth = 11; viewYear--; } loadHearings(); });
  qs("#cal-next").addEventListener("click", () => { viewMonth++; if (viewMonth > 11) { viewMonth = 0; viewYear++; } loadHearings(); });

  qs("#new-hearing-btn").addEventListener("click", async () => {
    if (!cases.length) await loadCases();
    const sel = qs("#nh-case");
    sel.innerHTML = "";
    cases.forEach((c) => sel.appendChild(el("option", { value: c.id }, [c.case_title])));
    ["nh-date", "nh-time", "nh-court", "nh-judge", "nh-notes"].forEach((id) => (qs("#" + id).value = ""));
    openModal("hearing-modal");
  });

  qs("#save-hearing-btn").addEventListener("click", async () => {
    const caseId = qs("#nh-case").value;
    const date = qs("#nh-date").value;
    if (!caseId) { toast("Please select a case", "error"); return; }
    if (!date) { toast("Please choose a date", "error"); return; }

    const payload = {
      case_id: Number(caseId),
      hearing_date: date,
      hearing_time: qs("#nh-time").value || null,
      court_name: qs("#nh-court").value,
      judge_name: qs("#nh-judge").value,
      notes: qs("#nh-notes").value,
    };

    const btn = qs("#save-hearing-btn");
    btn.disabled = true;
    try {
      const res = await fetch(window.HEARINGS_API_URL, {
        method: "POST",
        headers: jsonHeaders(),
        body: JSON.stringify(payload),
      });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not schedule hearing", "error");
        return;
      }
      closeModal("hearing-modal");
      toast("Hearing scheduled", "success");
      const scheduled = new Date(date + "T00:00:00");
      if (scheduled.getFullYear() !== viewYear || scheduled.getMonth() !== viewMonth) {
        viewYear = scheduled.getFullYear();
        viewMonth = scheduled.getMonth();
      }
      loadHearings();
    } catch (err) {
      toast("Could not schedule hearing. Please try again.", "error");
    } finally {
      btn.disabled = false;
    }
  });

  loadHearings();
  loadCases();
});
