/** Sidebar active state, user menu dropdown, notifications, mobile nav toggle. */
document.addEventListener("DOMContentLoaded", () => {
  function initialsFrom(name, email) {
    const parts = String(name || "").trim().split(/\s+/).filter(Boolean);
    if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return String(email || "?").slice(0, 2).toUpperCase();
  }

  // Prefer the signed-in user from Django; fall back to demo data only if absent.
  const user = window.CURRENT_USER;
  if (user) {
    const name = user.full_name || user.email || "User";
    const firm = user.law_firm_name || "Lexora";
    const email = user.email || "";
    const initials = initialsFrom(user.full_name, user.email);
    qsa("[data-user-name]").forEach((n) => (n.textContent = name));
    qsa("[data-user-email]").forEach((n) => (n.textContent = email));
    qsa("[data-user-firm]").forEach((n) => (n.textContent = firm));
    qsa("[data-user-initials]").forEach((n) => (n.textContent = initials));
  } else if (window.DEMO && DEMO.user) {
    qsa("[data-user-name]").forEach((n) => (n.textContent = DEMO.user.name));
    qsa("[data-user-email]").forEach((n) => (n.textContent = DEMO.user.email));
    qsa("[data-user-firm]").forEach((n) => (n.textContent = DEMO.user.firm));
    qsa("[data-user-initials]").forEach((n) => (n.textContent = DEMO.user.initials));
  }

  // Highlight active nav item based on body[data-page]
  const page = document.body.getAttribute("data-page");
  if (page) {
    qsa(".nav-item[data-nav]").forEach((item) => {
      item.classList.toggle("active", item.getAttribute("data-nav") === page);
    });
  }

  // Dropdown toggles (user menu, notifications, kebabs)
  qsa("[data-dropdown-toggle]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const menu = qs("#" + btn.getAttribute("data-dropdown-toggle"));
      if (!menu) return;
      const isOpen = menu.classList.contains("open");
      qsa(".dropdown-menu.open").forEach((m) => m.classList.remove("open"));
      if (!isOpen) menu.classList.add("open");
    });
  });
  document.addEventListener("click", () => qsa(".dropdown-menu.open").forEach((m) => m.classList.remove("open")));

  // Mobile sidebar toggle
  const mobileToggle = qs("[data-mobile-nav-toggle]");
  if (mobileToggle) {
    mobileToggle.addEventListener("click", () => qs(".sidebar").classList.toggle("open"));
  }
});
