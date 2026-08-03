document.addEventListener("DOMContentLoaded", () => {
  let cases = [...DEMO.cases];
  let activeFilter = "all";
  let searchTerm = "";
  let deletingId = null;

  const tbody = qs("#cases-table-body");
  const emptyState = qs("#cases-empty");

  function render() {
    const filtered = cases.filter((c) => {
      const matchesFilter = activeFilter === "all" || c.status === activeFilter;
      const haystack = `${c.title} ${c.client} ${c.number}`.toLowerCase();
      const matchesSearch = haystack.includes(searchTerm.toLowerCase());
      return matchesFilter && matchesSearch;
    });

    tbody.innerHTML = "";
    emptyState.classList.toggle("hidden", filtered.length > 0);

    filtered.forEach((c) => {
      const tr = el("tr", {}, [
        el("td", { onclick: () => (window.location.href = `/cases/${c.id}/`) }, [
          el("div", { class: "cell-primary" }, [c.title]),
          el("div", { class: "text-xs text-faint mono" }, [c.number]),
        ]),
        el("td", { class: "cell-muted", onclick: () => (window.location.href = `/cases/${c.id}/`) }, [c.type]),
        el("td", { onclick: () => (window.location.href = `/cases/${c.id}/`) }, [c.client]),
        el("td", { class: "cell-muted", onclick: () => (window.location.href = `/cases/${c.id}/`) }, [c.court.split(",")[0]]),
        el("td", { html: statusBadge(c.status), onclick: () => (window.location.href = `/cases/${c.id}/`) }),
        el("td", { class: "cell-muted", onclick: () => (window.location.href = `/cases/${c.id}/`) }, [c.hearingDate ? formatDateLong(c.hearingDate) : "—"]),
        el("td", { class: "cell-muted", onclick: () => (window.location.href = `/cases/${c.id}/`) }, [String(c.documents)]),
        (() => {
          const td = el("td", {});
          const dd = el("div", { class: "dropdown" });
          const btn = el("button", { class: "icon-btn btn-icon-only", onclick: (e) => e.stopPropagation() }, []);
          btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="5" r="1.4"/><circle cx="12" cy="12" r="1.4"/><circle cx="12" cy="19" r="1.4"/></svg>';
          const menu = el("div", { class: "dropdown-menu", style: "right:0; left:auto;" }, [
            el("a", { class: "dropdown-item", onclick: () => (window.location.href = `/cases/${c.id}/`) }, ["Open case"]),
            el("a", { class: "dropdown-item", onclick: () => openEditModal(c) }, ["Edit details"]),
            el("div", { class: "dropdown-sep" }),
            el("a", { class: "dropdown-item danger", onclick: () => askDelete(c) }, ["Delete case"]),
          ]);
          btn.addEventListener("click", (e) => {
            e.stopPropagation();
            qsa(".dropdown-menu.open").forEach((m) => (m !== menu ? m.classList.remove("open") : null));
            menu.classList.toggle("open");
          });
          dd.appendChild(btn); dd.appendChild(menu); td.appendChild(dd);
          return td;
        })(),
      ]);
      tbody.appendChild(tr);
    });
  }

  qs("#case-search").addEventListener("input", (e) => { searchTerm = e.target.value; render(); });
  qsa("[data-status-filter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      qsa("[data-status-filter]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      activeFilter = btn.getAttribute("data-status-filter");
      render();
    });
  });

  let editingId = null;
  function resetForm() {
    editingId = null;
    ["f-number", "f-title", "f-client", "f-opposite", "f-court", "f-hearing", "f-desc"].forEach((id) => (qs("#" + id).value = ""));
    qs("#f-type").value = "Criminal";
    qs("#f-status").value = "active";
    qs("#case-modal-title").textContent = "Create new case";
  }
  qs("#new-case-btn").addEventListener("click", () => { resetForm(); openModal("case-modal"); });

  window.openEditModal = function (c) {
    editingId = c.id;
    qs("#case-modal-title").textContent = "Edit case";
    qs("#f-number").value = c.number;
    qs("#f-title").value = c.title;
    qs("#f-type").value = c.type;
    qs("#f-status").value = c.status;
    qs("#f-client").value = c.client;
    qs("#f-opposite").value = c.opposite;
    qs("#f-court").value = c.court;
    qs("#f-hearing").value = c.hearingDate || "";
    qs("#f-desc").value = c.description;
    openModal("case-modal");
  };

  qs("#case-save-btn").addEventListener("click", () => {
    const title = qs("#f-title").value.trim();
    if (!title) { toast("Case title is required", "error"); return; }
    if (editingId) {
      const c = cases.find((x) => x.id === editingId);
      Object.assign(c, {
        number: qs("#f-number").value, title, type: qs("#f-type").value, status: qs("#f-status").value,
        client: qs("#f-client").value, opposite: qs("#f-opposite").value, court: qs("#f-court").value,
        hearingDate: qs("#f-hearing").value || null, description: qs("#f-desc").value,
      });
      toast("Case updated", "success");
    } else {
      cases.unshift({
        id: "new-" + Date.now(), number: qs("#f-number").value || "—", title, type: qs("#f-type").value,
        status: qs("#f-status").value, client: qs("#f-client").value, opposite: qs("#f-opposite").value,
        court: qs("#f-court").value, hearingDate: qs("#f-hearing").value || null, hearingTime: null,
        documents: 0, description: qs("#f-desc").value, updatedAt: "just now",
      });
      toast("Case created", "success");
    }
    closeModal("case-modal");
    render();
  });

  function askDelete(c) {
    deletingId = c.id;
    qs("#delete-case-name").textContent = c.title;
    openModal("delete-modal");
  }
  qs("#confirm-delete-btn").addEventListener("click", () => {
    cases = cases.filter((c) => c.id !== deletingId);
    closeModal("delete-modal");
    toast("Case deleted", "success");
    render();
  });

  render();
});
