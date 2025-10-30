(function () {
  const root = document.documentElement;
  const toggleBtn = document.getElementById("theme-toggle");
  const sunIcon = document.getElementById("icon-sun");
  const moonIcon = document.getElementById("icon-moon");

  // Load saved theme or fallback to system preference
  const savedTheme = localStorage.getItem("theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const initialTheme = savedTheme || (prefersDark ? "dark" : "light");

  // Apply theme
  root.setAttribute("data-theme", initialTheme);
  updateIcons(initialTheme);

  // Toggle click
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const current = root.getAttribute("data-theme");
      const next = current === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      localStorage.setItem("theme", next);
      updateIcons(next);
    });
  }

  function updateIcons(theme) {
    if (!sunIcon || !moonIcon) return;
    if (theme === "dark") {
      sunIcon.style.display = "inline-block";
      moonIcon.style.display = "none";
    } else {
      sunIcon.style.display = "none";
      moonIcon.style.display = "inline-block";
    }
  }
})();
