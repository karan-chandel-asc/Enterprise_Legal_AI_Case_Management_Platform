/** Sidebar active state, user menu dropdown, notifications, mobile nav toggle. */
document.addEventListener("DOMContentLoaded", () => {
  // Populate user chip(s) from demo data
  if (window.DEMO) {
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
