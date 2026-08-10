document.addEventListener("DOMContentLoaded", () => {
  function activate(name) {
    qsa("[data-settings-tab]").forEach((t) => t.classList.toggle("active", t.getAttribute("data-settings-tab") === name));
    qsa("[data-settings-panel]").forEach((p) => p.classList.toggle("active", p.getAttribute("data-settings-panel") === name));
    if (name === "security" || name === "mfa") {
      history.replaceState(null, "", "#" + name);
    } else {
      history.replaceState(null, "", location.pathname);
    }
  }

  qsa("[data-settings-tab]").forEach((t) => {
    t.addEventListener("click", () => activate(t.getAttribute("data-settings-tab")));
  });

  const hash = location.hash.replace("#", "");
  if (hash === "security" || hash === "mfa") activate(hash);
  else if (hash === "info") activate("info");

  function applyProfile(data) {
    if (!data) return;
    qs("#p-name").value = data.full_name || "";
    qs("#p-firm").value = data.law_firm_name || "";
    qs("#p-email").value = data.email || "";
    qs("#p-phone").value = data.phone_number || "";
    qs("#mfa-toggle").checked = !!data.mfa_enabled;
    qs("#mfa-email-hint").textContent = data.email
      ? `A 6-digit code will be sent to ${data.email} at each sign-in.`
      : "A 6-digit code will be sent to your email at each sign-in.";

    const name = data.full_name || data.email || "User";
    const initials = data.initials || name.slice(0, 2).toUpperCase();
    qsa("[data-user-name]").forEach((n) => (n.textContent = name));
    qsa("[data-user-email]").forEach((n) => (n.textContent = data.email || ""));
    qsa("[data-user-firm]").forEach((n) => (n.textContent = data.law_firm_name || "Lexora"));
    qsa("[data-user-initials]").forEach((n) => (n.textContent = initials));

    if (window.CURRENT_USER) {
      window.CURRENT_USER.full_name = data.full_name || "";
      window.CURRENT_USER.law_firm_name = data.law_firm_name || "";
      window.CURRENT_USER.phone_number = data.phone_number || "";
      window.CURRENT_USER.mfa_enabled = !!data.mfa_enabled;
    }
  }

  async function loadProfile() {
    try {
      const res = await fetch(window.PROFILE_API_URL, { headers: { Accept: "application/json" } });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not load profile", "error");
        return;
      }
      applyProfile(result.data);
    } catch (err) {
      toast("Could not load profile", "error");
    }
  }

  qs("#save-profile-btn").addEventListener("click", async () => {
    const payload = {
      full_name: qs("#p-name").value.trim(),
      law_firm_name: qs("#p-firm").value.trim(),
      phone_number: qs("#p-phone").value.trim(),
    };
    if (!payload.full_name) {
      toast("Full name is required", "error");
      return;
    }
    const btn = qs("#save-profile-btn");
    btn.disabled = true;
    try {
      const res = await fetch(window.PROFILE_API_URL, {
        method: "PATCH",
        headers: jsonHeaders(),
        body: JSON.stringify(payload),
      });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not update profile", "error");
        return;
      }
      applyProfile(result.data);
      toast(result.message || "Profile updated", "success");
    } catch (err) {
      toast("Could not update profile", "error");
    } finally {
      btn.disabled = false;
    }
  });

  qs("#save-password-btn").addEventListener("click", async () => {
    const current_password = qs("#cp-current").value;
    const new_password = qs("#cp-new").value;
    const confirm_password = qs("#cp-confirm").value;
    if (!current_password || !new_password) {
      toast("Please fill in all fields", "error");
      return;
    }
    if (new_password !== confirm_password) {
      toast("New passwords don't match", "error");
      return;
    }
    const btn = qs("#save-password-btn");
    btn.disabled = true;
    try {
      const res = await fetch(window.CHANGE_PASSWORD_API_URL, {
        method: "POST",
        headers: jsonHeaders(),
        body: JSON.stringify({ current_password, new_password, confirm_password }),
      });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not update password", "error");
        return;
      }
      toast(result.message || "Password updated", "success");
      ["cp-current", "cp-new", "cp-confirm"].forEach((id) => (qs("#" + id).value = ""));
    } catch (err) {
      toast("Could not update password", "error");
    } finally {
      btn.disabled = false;
    }
  });

  qs("#mfa-toggle").addEventListener("change", async (e) => {
    const enabled = e.target.checked;
    e.target.disabled = true;
    try {
      const res = await fetch(window.UPDATE_MFA_API_URL, {
        method: "POST",
        headers: jsonHeaders(),
        body: JSON.stringify({ enabled }),
      });
      const result = await res.json();
      if (!res.ok || !result.success) {
        e.target.checked = !enabled;
        toast(result.message || "Could not update MFA", "error");
        return;
      }
      applyProfile(result.data);
      toast(result.message || (enabled ? "Email OTP enabled" : "Email OTP disabled"), "success");
    } catch (err) {
      e.target.checked = !enabled;
      toast("Could not update MFA", "error");
    } finally {
      e.target.disabled = false;
    }
  });

  loadProfile();
});
