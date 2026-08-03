document.addEventListener("DOMContentLoaded", () => {
  function activate(name) {
    qsa("[data-settings-tab]").forEach((t) => t.classList.toggle("active", t.getAttribute("data-settings-tab") === name));
    qsa("[data-settings-panel]").forEach((p) => p.classList.toggle("active", p.getAttribute("data-settings-panel") === name));
  }
  qsa("[data-settings-tab]").forEach((t) => t.addEventListener("click", () => activate(t.getAttribute("data-settings-tab"))));

  const hash = location.hash.replace("#", "");
  if (hash && qs(`[data-settings-tab="${hash}"]`)) activate(hash);

  qs("#save-profile-btn").addEventListener("click", () => toast("Profile updated", "success"));

  qs("#save-password-btn").addEventListener("click", () => {
    if (!qs("#cp-current").value || !qs("#cp-new").value) { toast("Please fill in all fields", "error"); return; }
    if (qs("#cp-new").value !== qs("#cp-confirm").value) { toast("New passwords don't match", "error"); return; }
    toast("Password updated", "success");
    ["cp-current", "cp-new", "cp-confirm"].forEach((id) => (qs("#" + id).value = ""));
  });

  qs("#mfa-toggle").addEventListener("change", (e) => {
    toast(e.target.checked ? "Email OTP enabled" : "Email OTP disabled", "success");
  });

  qs("#change-photo-link").addEventListener("click", (e) => { e.preventDefault(); toast("Photo upload is a demo control"); });
});
