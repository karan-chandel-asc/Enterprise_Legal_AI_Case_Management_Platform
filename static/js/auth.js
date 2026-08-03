document.addEventListener("DOMContentLoaded", () => {
  // OTP boxes: auto-advance / backspace / paste full code
  qsa(".otp-box").forEach((box, i, all) => {
    box.addEventListener("input", () => {
      box.value = box.value.replace(/[^0-9]/g, "").slice(0, 1);
      if (box.value && all[i + 1]) all[i + 1].focus();
    });
    box.addEventListener("keydown", (e) => {
      if (e.key === "Backspace" && !box.value && all[i - 1]) all[i - 1].focus();
    });
    box.addEventListener("paste", (e) => {
      e.preventDefault();
      const digits = (e.clipboardData.getData("text") || "").replace(/[^0-9]/g, "").split("");
      all.forEach((b, idx) => (b.value = digits[idx] || ""));
      (all[Math.min(digits.length, all.length) - 1] || all[0]).focus();
    });
  });

  // Password visibility toggle
  qsa("[data-toggle-password]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const input = qs("#" + btn.getAttribute("data-toggle-password"));
      input.type = input.type === "password" ? "text" : "password";
    });
  });
});
