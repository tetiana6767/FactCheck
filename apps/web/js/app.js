(() => {
  "use strict";

  const claimInput = document.getElementById("claim");
  const checkButton = document.getElementById("check-button");
  const clearButton = document.getElementById("clear-button");
  const status = document.getElementById("status");
  const verdict = document.getElementById("verdict");
  const explanation = document.getElementById("explanation");
  const checkedClaim = document.getElementById("checked-claim");

  function setPending(isPending) {
    checkButton.disabled = isPending;
    clearButton.disabled = isPending;
    claimInput.disabled = isPending;
  }

  function renderReport(report) {
    verdict.textContent = report.verdict === "insufficient_evidence"
      ? "Недостатньо доказів"
      : report.verdict;
    explanation.textContent = report.explanation;
    checkedClaim.textContent = report.claim;
  }

  async function checkClaim() {
    const claim = claimInput.value.trim();
    if (!claim) {
      status.textContent = "Введіть текст перед перевіркою.";
      claimInput.focus();
      return;
    }

    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 10_000);
    setPending(true);
    status.textContent = "Надсилаємо твердження до API…";

    try {
      const response = await fetch("/api/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ claim }),
        signal: controller.signal,
      });
      if (!response.ok) {
        throw new Error(`API повернув HTTP ${response.status}`);
      }
      renderReport(await response.json());
      status.textContent = "Перевірку завершено.";
    } catch (error) {
      status.textContent = error.name === "AbortError"
        ? "Час очікування минув. Спробуйте ще раз."
        : "Не вдалося отримати результат. Перевірте роботу сервера.";
    } finally {
      window.clearTimeout(timeout);
      setPending(false);
    }
  }

  function clearForm() {
    claimInput.value = "";
    verdict.textContent = "Результату ще немає";
    explanation.textContent = "Після запиту тут з’явиться пояснення.";
    checkedClaim.textContent = "—";
    status.textContent = "Введіть текст для перевірки.";
    claimInput.focus();
  }

  checkButton.addEventListener("click", checkClaim);
  clearButton.addEventListener("click", clearForm);
})();
