(() => {
  "use strict";

  const claimInput = document.getElementById("claim");
  const checkButton = document.getElementById("check-button");
  const clearButton = document.getElementById("clear-button");
  const status = document.getElementById("status");
  const verdict = document.getElementById("verdict");
  const explanation = document.getElementById("explanation");
  const checkedClaim = document.getElementById("checked-claim");
  const claims = document.getElementById("claims");
  const evidence = document.getElementById("evidence");

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
    renderClaims(Array.isArray(report.claims) ? report.claims : []);
    const evidenceItems = report.evidence_snapshot?.items ?? report.evidence ?? [];
    renderEvidence(Array.isArray(evidenceItems) ? evidenceItems : []);
  }

  function emptyMessage(text) {
    const message = document.createElement("p");
    message.className = "empty-state";
    message.textContent = text;
    return message;
  }

  function renderClaims(items) {
    claims.replaceChildren();
    if (items.length === 0) {
      claims.append(emptyMessage("Перевірюваних тверджень не виділено."));
      return;
    }
    items.forEach((item) => {
      const article = document.createElement("article");
      article.className = "result-item";
      const identifier = document.createElement("span");
      identifier.className = "item-id";
      identifier.textContent = item.id;
      const text = document.createElement("p");
      text.textContent = item.text;
      article.append(identifier, text);
      claims.append(article);
    });
  }

  function renderEvidence(items) {
    evidence.replaceChildren();
    if (items.length === 0) {
      evidence.append(emptyMessage("У тестовому корпусі збігів немає."));
      return;
    }
    items.forEach((item) => {
      const article = document.createElement("article");
      article.className = "result-item";
      const heading = document.createElement("h4");
      heading.textContent = item.title;
      const relation = document.createElement("span");
      relation.className = "item-id";
      relation.textContent = `Для ${item.claim_id}`;
      const quote = document.createElement("blockquote");
      quote.textContent = item.quote || "Цитату не надано.";
      const source = document.createElement("p");
      source.className = "source-uri";
      source.textContent = item.url;
      article.append(heading, relation, quote, source);
      evidence.append(article);
    });
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
    claims.replaceChildren(emptyMessage("Твердження ще не виділялися."));
    evidence.replaceChildren(emptyMessage("Докази ще не шукалися."));
    status.textContent = "Введіть текст для перевірки.";
    claimInput.focus();
  }

  checkButton.addEventListener("click", checkClaim);
  clearButton.addEventListener("click", clearForm);
})();
