(() => {
  "use strict";

  const ready = (callback) => {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback, { once: true });
    } else {
      callback();
    }
  };

  ready(() => {
    const sidebar = document.getElementById("appSidebar");
    const backdrop = document.getElementById("sidebarBackdrop");
    const toggles = document.querySelectorAll("[data-sidebar-toggle]");

    const closeSidebar = () => {
      sidebar?.classList.remove("is-open");
      backdrop?.classList.remove("is-open");
      toggles.forEach((toggle) => toggle.setAttribute("aria-expanded", "false"));
      document.body.classList.remove("sidebar-open");
    };

    const openSidebar = () => {
      sidebar?.classList.add("is-open");
      backdrop?.classList.add("is-open");
      toggles.forEach((toggle) => toggle.setAttribute("aria-expanded", "true"));
      document.body.classList.add("sidebar-open");
    };

    toggles.forEach((toggle) => {
      toggle.addEventListener("click", () => {
        if (sidebar?.classList.contains("is-open")) {
          closeSidebar();
        } else {
          openSidebar();
        }
      });
    });

    backdrop?.addEventListener("click", closeSidebar);

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeSidebar();
    });

    window.addEventListener("resize", () => {
      if (window.innerWidth >= 992) closeSidebar();
    });

    document.querySelectorAll("[data-bs-toggle='tooltip']").forEach((element) => {
      if (window.bootstrap?.Tooltip) new window.bootstrap.Tooltip(element);
    });

    document.querySelectorAll("[data-auto-dismiss]").forEach((alert) => {
      const timeout = Number.parseInt(alert.dataset.autoDismiss || "6500", 10);
      window.setTimeout(() => {
        if (window.bootstrap?.Alert) {
          window.bootstrap.Alert.getOrCreateInstance(alert).close();
        }
      }, timeout);
    });

    document.querySelectorAll("[data-confirm]").forEach((element) => {
      element.addEventListener("click", (event) => {
        const message = element.dataset.confirm || "Continue with this action?";
        if (!window.confirm(message)) event.preventDefault();
      });
    });

    document.querySelectorAll("[data-password-toggle]").forEach((button) => {
      button.addEventListener("click", () => {
        const targetId = button.dataset.passwordToggle;
        const input = document.getElementById(targetId);
        if (!input) return;
        const reveal = input.type === "password";
        input.type = reveal ? "text" : "password";
        button.setAttribute("aria-pressed", reveal ? "true" : "false");
        const icon = button.querySelector("i");
        icon?.classList.toggle("bi-eye", !reveal);
        icon?.classList.toggle("bi-eye-slash", reveal);
      });
    });

    document.querySelectorAll("table[data-mobile-labels]").forEach((table) => {
      const labels = [...table.querySelectorAll("thead th")].map((cell) => cell.textContent.trim());
      table.querySelectorAll("tbody tr").forEach((row) => {
        row.querySelectorAll("td").forEach((cell, index) => {
          if (!cell.dataset.label && labels[index]) cell.dataset.label = labels[index];
        });
      });
    });
  });
})();
