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
  const multiAgentReport = document.getElementById("multi-agent-report");
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
    renderMultiAgentReport(report.multi_agent_report);
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
      const cost = run.cost_usd == null
        ? "вартість —"
        : `$${Number(run.cost_usd).toFixed(6)}`;
      metadata.textContent = `${model} · ${latency} мс · ${tokens} токенів · ${cost}`;
      article.append(metadata);
    }
    modelReport.append(article);
  }

  function renderMultiAgentReport(report) {
    multiAgentReport.replaceChildren();
    if (!report) {
      multiAgentReport.append(emptyMessage(
        "Мультиагентний граф вимкнено або ще не запускався.",
      ));
      return;
    }

    const roleLabels = {
      claim: "Твердження",
      evidence: "Докази",
      source: "Джерела",
      linguistic: "Мовний аналіз",
      skeptic: "Скептик",
      verifier: "Верифікатор",
      arbiter: "Арбітр",
    };
    const integral = report.integral || {};
    const overview = document.createElement("article");
    overview.className = "result-item agent-overview";
    const heading = document.createElement("h4");
    heading.textContent = report.execution_mode === "research"
      ? "Повний дослідницький режим"
      : "Економний режим";
    const metrics = document.createElement("dl");
    metrics.className = "metric-grid";
    [
      ["Інтегральна сила", integral.score],
      ["Покриття доказами", integral.coverage],
      ["Узгодженість", integral.consensus],
      ["Підтримка", integral.support],
      ["Спростування", integral.refutation],
    ].forEach(([label, value]) => {
      const term = document.createElement("dt");
      term.textContent = label;
      const definition = document.createElement("dd");
      definition.textContent = `${Math.round(Number(value || 0) * 100)}%`;
      metrics.append(term, definition);
    });
    const cost = document.createElement("p");
    cost.className = "item-id";
    cost.textContent = `Загальна вартість: $${Number(
      report.total_cost_usd || 0,
    ).toFixed(6)}`;
    overview.append(heading, metrics, cost);
    multiAgentReport.append(overview);

    (report.role_results || []).forEach((result) => {
      const article = document.createElement("article");
      article.className = "result-item agent-role";
      const title = document.createElement("h4");
      title.textContent = roleLabels[result.role] || result.role;
      const summary = document.createElement("p");
      summary.textContent = result.analysis?.summary
        || `Роль не завершена: ${result.run?.error_code || "невідома помилка"}.`;
      const metadata = document.createElement("p");
      metadata.className = "item-id";
      metadata.textContent = [
        result.run?.model || "модель не визначена",
        result.run?.status || "без статусу",
        result.run?.total_tokens == null
          ? "токени —"
          : `${result.run.total_tokens} токенів`,
      ].join(" · ");
      article.append(title, summary, metadata);
      multiAgentReport.append(article);
    });

    const skipped = (report.skipped_roles || []).map(
      (role) => roleLabels[role] || role,
    );
    if (skipped.length > 0) {
      multiAgentReport.append(emptyMessage(
        `Пропущені економною політикою ролі: ${skipped.join(", ")}.`,
      ));
    }
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
    const timeout = window.setTimeout(() => controller.abort(), 120_000);
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
    multiAgentReport.replaceChildren(
      emptyMessage("Мультиагентний граф ще не запускався."),
    );
    claims.replaceChildren(emptyMessage("Твердження ще не виділялися."));
    evidence.replaceChildren(emptyMessage("Докази ще не шукалися."));
    status.textContent = "Введіть текст для перевірки.";
    claimInput.focus();
  }

  checkButton.addEventListener("click", checkClaim);
  clearButton.addEventListener("click", clearForm);
})();
