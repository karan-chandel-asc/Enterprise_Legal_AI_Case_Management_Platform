/** Wires the shared "create case" modal (in base_app.html) to the topbar's
 * "New Case" button so it works from every page, not just Dashboard/Cases.
 *
 * Pages that need their own save logic (e.g. the Cases list page also
 * supports editing through this same modal) set `window.CASE_MODAL_HANDLED
 * = true` before this file runs, so this script only opens the modal for
 * them and leaves saving to the page's own script. Everywhere else, this
 * file also handles the save itself and lands you on the new case's page.
 */
document.addEventListener("DOMContentLoaded", () => {
  const modal = qs("#case-modal");
  if (!modal) return;

  function resetCreateCaseForm() {
    ["f-number", "f-title", "f-client", "f-opposite", "f-court", "f-hearing", "f-desc"].forEach((id) => {
      const input = qs("#" + id);
      if (input) input.value = "";
    });
    const type = qs("#f-type");
    if (type) type.value = "criminal";
    const statusField = qs("#f-status");
    if (statusField) statusField.value = "active";
    const title = qs("#case-modal-title");
    if (title) title.textContent = "Create new case";
  }

  window.openCreateCaseModal = function () {
    resetCreateCaseForm();
    // Lets pages with their own edit-mode state (e.g. Cases list, which
    // tracks an `editingId`) know a fresh create was requested, so they
    // don't accidentally PATCH a case that was being edited earlier.
    document.dispatchEvent(new CustomEvent("case-modal:create"));
    openModal("case-modal");
  };

  const topbarBtn = qs("#topbar-new-case-btn");
  if (topbarBtn) {
    topbarBtn.addEventListener("click", (e) => {
      e.preventDefault();
      window.openCreateCaseModal();
    });
  }

  if (window.CASE_MODAL_HANDLED) return;

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
      window.location.href = `/cases/${result.data.id}/`;
    } catch (err) {
      toast("Could not save case. Please try again.", "error");
    } finally {
      saveBtn.disabled = false;
    }
  });
});
