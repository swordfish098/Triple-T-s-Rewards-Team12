document.addEventListener("DOMContentLoaded", () => {
    const submenuToggles = document.querySelectorAll(".submenu-toggle");
  
    submenuToggles.forEach((toggle) => {
      const targetId = toggle.getAttribute("data-target");
      const targetMenu = document.getElementById(targetId);
      if (!targetMenu) return;
  
      // make sure we start collapsed
      if (!targetMenu.classList.contains("collapsed")) {
        targetMenu.style.height = "0";
        targetMenu.classList.add("collapsed");
      }
  
      let isAnimating = false;
  
      toggle.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (isAnimating) return; // prevent double triggers
        isAnimating = true;
  
        const isCollapsed = targetMenu.classList.contains("collapsed");
  
        if (isCollapsed) {
          // EXPAND
          targetMenu.classList.remove("collapsed");
          const fullHeight = targetMenu.scrollHeight + "px";
          targetMenu.style.height = fullHeight;
          toggle.classList.add("expanded");
          targetMenu.addEventListener(
            "transitionend",
            () => {
              targetMenu.style.height = "auto";
              isAnimating = false;
            },
            { once: true }
          );
        } else {
          // COLLAPSE
          const currentHeight = targetMenu.scrollHeight + "px";
          targetMenu.style.height = currentHeight;
          // force reflow
          targetMenu.offsetHeight;
          targetMenu.style.height = "0";
          toggle.classList.remove("expanded");
          targetMenu.addEventListener(
            "transitionend",
            () => {
              targetMenu.classList.add("collapsed");
              isAnimating = false;
            },
            { once: true }
          );
        }
      });
    });
  });
  