(() => {
  "use strict";

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-table-search]").forEach((input) => {
      const tableId = input.dataset.tableSearch;
      const table = document.getElementById(tableId);
      if (!table) return;
      const rows = [...table.querySelectorAll("tbody tr")];
      input.addEventListener("input", () => {
        const term = input.value.trim().toLowerCase();
        rows.forEach((row) => {
          row.hidden = Boolean(term) && !row.textContent.toLowerCase().includes(term);
        });
      });
    });
  });
})();
