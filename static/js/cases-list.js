// This page has its own create/edit save logic for the shared case modal
// (it can PATCH an existing case, not just POST a new one), so tell
// global-case-modal.js not to also bind its own generic save handler.
window.CASE_MODAL_HANDLED = true;

document.addEventListener("DOMContentLoaded", () => {
  let cases = [];
  let activeFilter = "all";
  let searchTerm = "";
  let currentPage = 1;
  let pagination = { page: 1, total_pages: 1, has_next: false, has_previous: false, total_results: 0 };
  let deletingId = null;
  let searchDebounce = null;

  const tbody = qs("#cases-table-body");
  const emptyState = qs("#cases-empty");
  const paginationInfo = qs("#cases-pagination-info");
  const pageIndicator = qs("#cases-page-indicator");
  const prevBtn = qs("#cases-prev-btn");
  const nextBtn = qs("#cases-next-btn");

  function mapCase(c) {
    return {
      id: c.id,
      number: c.case_id,
      title: c.case_title,
      type: c.case_type ? c.case_type[0].toUpperCase() + c.case_type.slice(1) : "—",
      typeRaw: c.case_type,
      status: c.case_status,
      client: c.client_name,
      opposite: c.opposing_party_name,
      court: c.court_name,
      hearingDate: c.hearing_date,
      documents: c.document_count,
      description: c.case_description,
    };
  }

  function buildQuery() {
    const params = new URLSearchParams();
    if (searchTerm) params.set("search", searchTerm);
    if (activeFilter !== "all") params.set("case_status", activeFilter);
    params.set("page", currentPage);
    params.set("page_size", 10);
    return params.toString();
  }

  async function loadCases() {
    try {
      const res = await fetch(`${window.CASES_LIST_API_URL}?${buildQuery()}`, {
        headers: { Accept: "application/json" },
      });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not load cases", "error");
        return;
      }

      const data = result.data || {};
      cases = (data.cases || []).map(mapCase);
      pagination = data.pagination || pagination;
      currentPage = pagination.page || 1;

      const counts = data.counts || {};
      const subtitle = qs(".page-head .titles p");
      if (subtitle) subtitle.textContent = `${counts.total ?? 0} cases · ${counts.active ?? 0} active`;

      render();
      renderPagination();
    } catch (err) {
      toast("Could not load cases. Please refresh.", "error");
    }
  }

  function renderPagination() {
    const { page, total_pages, total_results, has_next, has_previous } = pagination;
    paginationInfo.textContent = total_results
      ? `Page ${page} of ${total_pages} · ${total_results} result${total_results === 1 ? "" : "s"}`
      : "No results";
    pageIndicator.textContent = `${page} / ${Math.max(total_pages, 1)}`;
    prevBtn.disabled = !has_previous;
    nextBtn.disabled = !has_next;
  }

  function render() {
    tbody.innerHTML = "";
    emptyState.classList.toggle("hidden", cases.length > 0);

    cases.forEach((c) => {
      const tr = el("tr", {}, [
        el("td", { onclick: () => (window.location.href = `/cases/${c.id}/`) }, [
          el("div", { class: "cell-primary" }, [c.title]),
          el("div", { class: "text-xs text-faint mono" }, [c.number]),
        ]),
        el("td", { class: "cell-muted", onclick: () => (window.location.href = `/cases/${c.id}/`) }, [c.type]),
        el("td", { onclick: () => (window.location.href = `/cases/${c.id}/`) }, [c.client]),
        el("td", { class: "cell-muted", onclick: () => (window.location.href = `/cases/${c.id}/`) }, [c.court.split(",")[0]]),
        el("td", { html: statusBadge(c.status), onclick: () => (window.location.href = `/cases/${c.id}/`) }),
        el("td", { class: "cell-muted", onclick: () => (window.location.href = `/cases/${c.id}/`) }, [c.hearingDate || "—"]),
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

  qs("#case-search").addEventListener("input", (e) => {
    searchTerm = e.target.value;
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(() => {
      currentPage = 1;
      loadCases();
    }, 300);
  });

  qsa("[data-status-filter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      qsa("[data-status-filter]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      activeFilter = btn.getAttribute("data-status-filter");
      currentPage = 1;
      loadCases();
    });
  });

  prevBtn.addEventListener("click", () => {
    if (!pagination.has_previous) return;
    currentPage -= 1;
    loadCases();
  });
  nextBtn.addEventListener("click", () => {
    if (!pagination.has_next) return;
    currentPage += 1;
    loadCases();
  });

  let editingId = null;
  function resetForm() {
    editingId = null;
    ["f-number", "f-title", "f-client", "f-opposite", "f-court", "f-hearing", "f-desc"].forEach((id) => (qs("#" + id).value = ""));
    qs("#f-type").value = "criminal";
    qs("#f-status").value = "active";
    qs("#case-modal-title").textContent = "Create new case";
  }
  // "New Case" is opened via the shared topbar button (base_app.html +
  // global-case-modal.js); this just makes sure `editingId` is cleared
  // whenever that happens, so Save doesn't accidentally PATCH a case that
  // was being edited earlier.
  document.addEventListener("case-modal:create", () => { editingId = null; });

  window.openEditModal = function (c) {
    editingId = c.id;
    qs("#case-modal-title").textContent = "Edit case";
    qs("#f-number").value = c.number;
    qs("#f-title").value = c.title;
    qs("#f-type").value = c.typeRaw || c.type.toLowerCase();
    qs("#f-status").value = c.status;
    qs("#f-client").value = c.client;
    qs("#f-opposite").value = c.opposite;
    qs("#f-court").value = c.court;
    qs("#f-hearing").value = c.hearingDate || "";
    qs("#f-desc").value = c.description;
    openModal("case-modal");
  };

  function caseDetailApiUrl(id) {
    return window.CASE_DETAIL_API_URL_TEMPLATE.replace("0", id);
  }

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
      const isEdit = !!editingId;
      const res = await fetch(isEdit ? caseDetailApiUrl(editingId) : window.CASES_CREATE_API_URL, {
        method: isEdit ? "PATCH" : "POST",
        headers: jsonHeaders(),
        body: JSON.stringify(payload),
      });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || `Could not ${isEdit ? "update" : "create"} case`, "error");
        return;
      }
      toast(isEdit ? "Case updated" : "Case created", "success");
      closeModal("case-modal");
      if (!isEdit) currentPage = 1;
      loadCases();
    } catch (err) {
      toast("Could not save case. Please try again.", "error");
    } finally {
      saveBtn.disabled = false;
    }
  });

  function askDelete(c) {
    deletingId = c.id;
    qs("#delete-case-name").textContent = c.title;
    openModal("delete-modal");
  }
  qs("#confirm-delete-btn").addEventListener("click", async () => {
    const btn = qs("#confirm-delete-btn");
    btn.disabled = true;
    try {
      const res = await fetch(caseDetailApiUrl(deletingId), { method: "DELETE", headers: jsonHeaders() });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not delete case", "error");
        return;
      }
      closeModal("delete-modal");
      toast("Case deleted", "success");
      loadCases();
    } catch (err) {
      toast("Could not delete case. Please try again.", "error");
    } finally {
      btn.disabled = false;
    }
  });

  loadCases();
});
