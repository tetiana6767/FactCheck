const ROLE_LABELS = {
  claim: "Агент тверджень",
  evidence: "Агент доказів",
  source: "Агент джерел",
  linguistic: "Мовний аналітик",
  skeptic: "Скептик",
  verifier: "Верифікатор",
  arbiter: "Арбітр",
};

const STATUS_LABELS = {
  supported: "Підтверджено",
  refuted: "Спростовано",
  conflicting: "Суперечливі докази",
  insufficient_evidence: "Недостатньо доказів",
};

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function emptyMessage(text) { return element("p", "empty-state", text); }
function percent(value) { return `${Math.round(Number(value || 0) * 100)}%`; }

function deriveRisk(report) {
  const multi = report.multi_agent_report;
  const integral = multi?.integral || {};
  const highRisk = (multi?.role_results || []).some((item) => item.analysis?.high_risk);
  const conflict = Number(integral.support || 0) > 0 && Number(integral.refutation || 0) > 0;
  let value = Number(integral.risk_score ?? 1);
  if (highRisk || conflict) value = Math.max(value, 0.67);
  const label = value >= 0.67 ? "Високий ризик" : value >= 0.34 ? "Середній ризик" : "Низький ризик";
  const className = value >= 0.67 ? "risk-high" : value >= 0.34 ? "risk-medium" : "risk-low";
  return { label: `${label}: ${percent(value)}`, className };
}

function renderSummary(report) {
  const integral = report.multi_agent_report?.integral || {};
  const score = Math.round(Number(integral.trust_score || 0) * 100);
  const risk = deriveRisk(report);
  document.getElementById("confidence-ring").style.setProperty("--score", score);
  document.getElementById("confidence-value").textContent = `${score}%`;
  const titles = {
    supported: "Знайдені докази підтримують твердження",
    refuted: "Знайдені докази спростовують твердження",
    conflicting: "Джерела суперечать одне одному",
    insufficient_evidence: "Потрібні додаткові надійні джерела",
  };
  document.getElementById("confidence-title").textContent = titles[report.verdict] || titles.insufficient_evidence;
  document.getElementById("verdict").textContent = STATUS_LABELS[report.verdict] || "Результат потребує пояснення";
  const riskNode = document.getElementById("risk-level");
  riskNode.className = `risk-badge ${risk.className}`;
  riskNode.textContent = risk.label;
  document.getElementById("explanation").textContent = report.explanation;
  document.getElementById("checked-claim").textContent = report.claim;
}

function claimAssessment(report, claimId) {
  const results = [...(report.multi_agent_report?.role_results || [])].reverse();
  for (const result of results) {
    const assessment = result.analysis?.claim_assessments?.find((item) => item.claim_id === claimId);
    if (assessment) return assessment;
  }
  return null;
}

function claimWarnings(claim, report) {
  const flags = report.linguistic_flags || [];
  const text = claim.text.toLocaleLowerCase("uk-UA");
  return flags.filter((flag) => {
    const fragment = String(flag.fragment || "").toLocaleLowerCase("uk-UA");
    return fragment && (text.includes(fragment) || fragment.includes(text));
  });
}

function renderClaims(items, report) {
  const container = document.getElementById("claims");
  document.getElementById("claims-count").textContent = items.length;
  container.replaceChildren();
  if (!items.length) return container.append(emptyMessage("Перевірюваних тверджень не виділено."));
  items.forEach((item, index) => {
    const card = element("article", "result-item claim-item");
    const content = element("div");
    const assessment = claimAssessment(report, item.id);
    const sources = (report.evidence_snapshot?.items || report.evidence || []).filter((source) => source.claim_id === item.id);
    const warnings = claimWarnings(item, report);
    content.append(
      element("span", "item-id", `Твердження ${index + 1}`),
      element("p", "", item.text),
      element("span", "status-chip", STATUS_LABELS[assessment?.status] || "Потребує перевірки"),
      element("p", "claim-rationale", assessment?.rationale || (sources.length
        ? "Джерела знайдено, але остаточну оцінку агента ще не сформовано."
        : "Для цієї тези не знайдено надійного підтвердження. Довіряти їй без додаткової перевірки ризиковано.")),
    );
    if (warnings.length) {
      const list = element("ul", "uncertainty-list");
      warnings.forEach((warning) => list.append(element("li", "", warning.explanation)));
      content.append(element("h4", "", "Що виглядає підозріло"), list);
    }
    content.append(element("p", "agent-meta", `Пов'язаних джерел: ${sources.length}`));
    card.append(element("span", "claim-number", `${index + 1}`), content);
    container.append(card);
  });
}

function appendSource(container, item) {
  const source = element("p", "source-uri");
  if (/^https?:\/\//i.test(item.url)) {
    const link = element("a", "", item.url);
    link.href = item.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    source.append(link);
  } else source.textContent = item.url;
  container.append(source);
}

function evidenceUsage(item, report) {
  const assessment = claimAssessment(report, item.claim_id);
  if (!assessment?.evidence_ids?.includes(item.id)) return "Джерело для перевірки";
  const labels = {
    supported: "Використано для підтвердження",
    refuted: "Використано для спростування",
    conflicting: "Суперечливий доказ",
    insufficient_evidence: "Потребує додаткової перевірки",
  };
  return labels[assessment.status] || "Джерело для перевірки";
}

function renderEvidence(items, report) {
  const container = document.getElementById("evidence");
  document.getElementById("evidence-count").textContent = items.length;
  container.replaceChildren();
  if (!items.length) {
    return container.append(emptyMessage("У поточному корпусі збігів немає. Це не означає, що твердження неправдиве."));
  }
  items.forEach((item) => {
    const card = element("article", "result-item");
    const claimNumber = item.claim_id?.replace(/^claim-/, "") || "—";
    card.append(
      element("span", "item-id", `Доказ для твердження ${claimNumber}`),
      element("span", "status-chip", evidenceUsage(item, report)),
      element("h4", "", item.title),
      element("blockquote", "", item.quote || "Цитату не надано."),
    );
    appendSource(card, item);
    container.append(card);
  });
}

function renderMetrics(multi) {
  const container = document.getElementById("agent-overview");
  container.replaceChildren();
  const integral = multi?.integral || {};
  [["Рівень довіри", integral.trust_score ?? 0], ["Ризик довіряти", integral.risk_score ?? 1], ["Сила доказів", integral.score ?? 0], ["Покриття", integral.coverage ?? 0], ["Узгодженість", integral.consensus ?? 0]].forEach(([label, value]) => {
    const card = element("div", "metric-card");
    card.append(element("strong", "", percent(value)), element("span", "", label));
    container.append(card);
  });
}

function renderAssessment(assessment) {
  const section = element("div", "assessment");
  const status = STATUS_LABELS[assessment.status] || "Статус уточнюється";
  section.append(element("span", "status-chip", status), element("p", "", assessment.rationale));
  if (assessment.evidence_ids?.length) section.append(element("p", "agent-meta", `Докази: ${assessment.evidence_ids.join(", ")}`));
  return section;
}

function renderAgents(multi) {
  const container = document.getElementById("multi-agent-report");
  container.replaceChildren();
  renderMetrics(multi);
  if (!multi) return container.append(emptyMessage("Мультиагентний аналіз не запускався."));
  (multi.role_results || []).forEach((result) => {
    const details = element("details", "result-item agent-role");
    const body = element("div", "agent-body");
    body.append(element("p", "", result.analysis?.summary || "Агент не завершив аналіз."));
    if (result.analysis) {
      body.append(element("p", "agent-meta", `Впевненість агента: ${percent(result.analysis.confidence)}${result.analysis.high_risk ? " · позначено високий ризик" : ""}`));
      result.analysis.claim_assessments.forEach((item) => body.append(renderAssessment(item)));
      if (result.analysis.uncertainties?.length) {
        const list = element("ul", "uncertainty-list");
        result.analysis.uncertainties.forEach((item) => list.append(element("li", "", item)));
        body.append(element("h4", "", "Що лишилося невизначеним"), list);
      }
    }
    details.append(element("summary", "", ROLE_LABELS[result.role] || "Спеціалізований агент"), body);
    container.append(details);
  });
  if (multi.skipped_roles?.length) {
    const labels = multi.skipped_roles.map((role) => ROLE_LABELS[role] || "спеціалізований агент");
    container.append(emptyMessage(`Економний режим пропустив ролі: ${labels.join(", ")}.`));
  }
}

function renderSignals(items) {
  const container = document.getElementById("linguistic-flags");
  container.replaceChildren();
  if (!items.length) return container.append(emptyMessage("Явних мовних сигналів не виявлено."));
  items.forEach((item) => {
    const card = element("article", "result-item");
    card.append(element("strong", "", item.fragment), element("p", "", item.explanation));
    container.append(card);
  });
}

function renderModel(run, analysis) {
  const container = document.getElementById("model-report");
  container.replaceChildren();
  const card = element("article", "result-item");
  const messages = { not_configured: "Модельний сервіс не налаштовано; локальний аналіз доступний.", timeout: "Модель не відповіла вчасно.", invalid_response: "Відповідь моделі не пройшла перевірку формату.", provider_error: "Провайдер моделі тимчасово недоступний." };
  card.append(element("p", "", run?.status === "completed" ? analysis?.summary || "Структурований аналіз завершено." : messages[run?.status] || "Модель не запускалася."));
  if (run?.status === "completed") {
    const cost = run.cost_usd == null ? "вартість не надано" : `$${Number(run.cost_usd).toFixed(6)}`;
    card.append(element("p", "agent-meta", `${run.model || "Модель"} · ${run.total_tokens ?? "—"} токенів · ${cost}`));
  }
  container.append(card);
}

export function renderReport(report) {
  const claims = Array.isArray(report.claims) ? report.claims : [];
  const evidence = report.evidence_snapshot?.items ?? report.evidence ?? [];
  renderSummary(report);
  renderClaims(claims, report);
  renderEvidence(Array.isArray(evidence) ? evidence : [], report);
  renderAgents(report.multi_agent_report);
  renderSignals(Array.isArray(report.linguistic_flags) ? report.linguistic_flags : []);
  renderModel(report.model_run, report.agent_analysis);
  document.getElementById("report").hidden = false;
}
