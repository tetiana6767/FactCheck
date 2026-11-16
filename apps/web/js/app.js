(() => {
  "use strict";

  const claimInput = document.getElementById("claim");
  const checkButton = document.getElementById("check-button");
  const clearButton = document.getElementById("clear-button");
  const status = document.getElementById("status");
  const verdict = document.getElementById("verdict");
  const explanation = document.getElementById("explanation");
  const checkedClaim = document.getElementById("checked-claim");
  const linguisticFlags = document.getElementById("linguistic-flags");
  const modelReport = document.getElementById("model-report");
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
    renderLinguisticFlags(
      Array.isArray(report.linguistic_flags) ? report.linguistic_flags : [],
    );
    renderModelReport(report.model_run, report.agent_analysis);
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

  function renderLinguisticFlags(items) {
    linguisticFlags.replaceChildren();
    if (items.length === 0) {
      linguisticFlags.append(emptyMessage("Явних мовних сигналів не виявлено."));
      return;
    }
    items.forEach((item) => {
      const article = document.createElement("article");
      article.className = "result-item";
      const fragment = document.createElement("strong");
      fragment.textContent = item.fragment;
      const explanation = document.createElement("p");
      explanation.textContent = item.explanation;
      article.append(fragment, explanation);
      linguisticFlags.append(article);
    });
  }

  function renderModelReport(run, analysis) {
    modelReport.replaceChildren();
    const messages = {
      not_configured: "OpenRouter не налаштовано. Локальний аналіз доступний.",
      timeout: "Модель не відповіла вчасно. Спробуйте повторити запит.",
      invalid_response: "Модель повернула відповідь невідомого формату.",
      provider_error: "Провайдер моделі тимчасово недоступний.",
    };
    const article = document.createElement("article");
    article.className = "result-item";
    const statusText = document.createElement("p");
    statusText.textContent = run?.status === "completed"
      ? analysis?.summary || "Структурований аналіз завершено."
      : messages[run?.status] || "Модель ще не запускалася.";
    article.append(statusText);

    if (run?.status === "completed") {
      const metadata = document.createElement("p");
      metadata.className = "item-id";
      const model = run.model || "невідома модель";
      const latency = run.latency_ms ?? "—";
      const tokens = run.total_tokens ?? "—";
      metadata.textContent = `${model} · ${latency} мс · ${tokens} токенів`;
      article.append(metadata);
    }
    modelReport.append(article);
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
    const timeout = window.setTimeout(() => controller.abort(), 45_000);
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
    linguisticFlags.replaceChildren(
      emptyMessage("Мовний аналіз ще не виконувався."),
    );
    modelReport.replaceChildren(emptyMessage("Модель ще не запускалася."));
    claims.replaceChildren(emptyMessage("Твердження ще не виділялися."));
    evidence.replaceChildren(emptyMessage("Докази ще не шукалися."));
    status.textContent = "Введіть текст для перевірки.";
    claimInput.focus();
  }

  checkButton.addEventListener("click", checkClaim);
  clearButton.addEventListener("click", clearForm);
})();
