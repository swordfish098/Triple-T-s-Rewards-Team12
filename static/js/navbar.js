/* =========================================================
   Triple T's Rewards – Navbar + Theme Control
   Handles: user menu dropdown, theme persistence, sidebar toggle
   ========================================================= */
document.addEventListener("DOMContentLoaded", () => {
  // === User menu toggle ===
  const userMenuToggle = document.querySelector(".user-menu-toggle");
  const userMenu = document.querySelector(".user-menu");

  if (userMenuToggle && userMenu) {
    userMenuToggle.addEventListener("click", (e) => {
      e.stopPropagation();
      userMenu.classList.toggle("open");
      const expanded = userMenu.classList.contains("open");
      userMenuToggle.setAttribute("aria-expanded", expanded);
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", () => {
      userMenu.classList.remove("open");
      userMenuToggle.setAttribute("aria-expanded", "false");
    });
  }

  // === Sidebar toggle (if present) ===
  const sidebarToggle = document.querySelector(".sidebar-toggle");
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", () => {
      document.body.classList.toggle("is-sidebar-open");
    });
  }

  // === Theme toggle & persistence ===
  const themeCheckbox = document.getElementById("themeToggle");
  const themeLabel = document.querySelector(".theme-label");
  const currentTheme = localStorage.getItem("theme") || "light";

  // Apply saved theme to <html> via data-theme
  document.documentElement.setAttribute("data-theme", currentTheme);
  if (themeCheckbox) themeCheckbox.checked = currentTheme === "dark";

  // Update label text
  if (themeLabel) {
    themeLabel.textContent = currentTheme === "dark" ? "Dark Mode" : "Light Mode";
  }

  // Toggle theme on change
  if (themeCheckbox) {
    themeCheckbox.addEventListener("change", () => {
      const newTheme = themeCheckbox.checked ? "dark" : "light";
      document.documentElement.setAttribute("data-theme", newTheme);
      localStorage.setItem("theme", newTheme);
      if (themeLabel) {
        themeLabel.textContent = newTheme === "dark" ? "Dark Mode" : "Light Mode";
      }
    });
  }
});