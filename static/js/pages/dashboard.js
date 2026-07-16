(() => {
  "use strict";
  document.addEventListener("DOMContentLoaded", () => {
    const greeting = document.querySelector("[data-time-greeting]");
    if (!greeting) return;
    const hour = new Date().getHours();
    greeting.textContent = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  });
})();
