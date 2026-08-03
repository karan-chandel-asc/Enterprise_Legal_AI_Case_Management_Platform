document.addEventListener("DOMContentLoaded", () => {
  let hearings = [...DEMO.hearings];
  let viewYear = 2026, viewMonth = 7; // August 2026 — matches the seeded hearing dates
  const today = new Date(2026, 7, 3);
  const MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

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
    [...hearings].sort((a, b) => a.date.localeCompare(b.date)).forEach((h) => {
      const { day, month } = formatDateShort(h.date);
      box.appendChild(el("div", { class: "hearing-list-item", onclick: () => openHearing(h) }, [
        el("div", { class: "hearing-date-block" }, [el("div", { class: "d" }, [String(day)]), el("div", { class: "m" }, [month])]),
        el("div", { class: "flex-1" }, [
          el("b", { style: "display:block;font-size:13px;" }, [h.caseTitle]),
          el("span", { class: "text-sm text-muted" }, [`${h.time} · ${h.court.split(",")[0]}`]),
          el("div", { style: "margin-top:4px;", html: statusBadge(h.status === "urgent" ? "urgent" : "confirmed") }),
        ]),
      ]));
    });
  }

  function openHearing(h) {
    qs("#ho-case-tag").textContent = h.caseId.toUpperCase();
    qs("#ho-title").textContent = h.caseTitle;
    qs("#ho-status").innerHTML = statusBadge(h.status === "urgent" ? "urgent" : "confirmed");
    qs("#ho-datetime").textContent = `${formatDateLong(h.date)} · ${h.time}`;
    qs("#ho-court").textContent = h.court;
    qs("#ho-judge").textContent = h.judge;
    qs("#ho-notes").textContent = h.notes || "No notes added.";
    qs("#ho-open-case").setAttribute("href", `/cases/${h.caseId}/`);
    qs("#hearing-slideover").classList.add("open");
  }

  qs("#cal-prev").addEventListener("click", () => { viewMonth--; if (viewMonth < 0) { viewMonth = 11; viewYear--; } renderCalendar(); });
  qs("#cal-next").addEventListener("click", () => { viewMonth++; if (viewMonth > 11) { viewMonth = 0; viewYear++; } renderCalendar(); });

  qs("#new-hearing-btn").addEventListener("click", () => {
    const sel = qs("#nh-case");
    sel.innerHTML = "";
    DEMO.cases.forEach((c) => sel.appendChild(el("option", { value: c.id }, [c.title])));
    ["nh-date", "nh-time", "nh-court", "nh-judge", "nh-notes"].forEach((id) => (qs("#" + id).value = ""));
    openModal("hearing-modal");
  });
  qs("#save-hearing-btn").addEventListener("click", () => {
    const caseId = qs("#nh-case").value;
    const c = DEMO.cases.find((x) => x.id === caseId);
    const date = qs("#nh-date").value;
    if (!date) { toast("Please choose a date", "error"); return; }
    hearings.push({
      id: "h" + Date.now(), caseId, caseTitle: c.title, date,
      time: qs("#nh-time").value || "10:00 AM", court: qs("#nh-court").value || c.court,
      judge: qs("#nh-judge").value || c.judge, status: "confirmed", notes: qs("#nh-notes").value,
    });
    closeModal("hearing-modal");
    renderCalendar();
    renderList();
    toast("Hearing scheduled", "success");
  });

  renderCalendar();
  renderList();
});
