(() => {
  "use strict";

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("form[data-prevent-double-submit]").forEach((form) => {
      form.addEventListener("submit", () => {
        const submitters = form.querySelectorAll("button[type='submit'], input[type='submit']");
        submitters.forEach((submitter) => {
          submitter.disabled = true;
          if (submitter.tagName === "BUTTON") {
            submitter.dataset.originalText = submitter.innerHTML;
            submitter.innerHTML = '<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>Processing…';
          }
        });
      });
    });

    document.querySelectorAll("textarea[data-character-count]").forEach((textarea) => {
      const counterId = `${textarea.id}-counter`;
      let counter = document.getElementById(counterId);
      if (!counter) {
        counter = document.createElement("div");
        counter.id = counterId;
        counter.className = "form-text text-end";
        textarea.insertAdjacentElement("afterend", counter);
      }
      const update = () => {
        const max = textarea.maxLength > 0 ? ` / ${textarea.maxLength}` : "";
        counter.textContent = `${textarea.value.length}${max} characters`;
      };
      textarea.addEventListener("input", update);
      update();
    });
  });
})();
