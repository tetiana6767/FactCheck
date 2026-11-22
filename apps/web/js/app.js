import { renderReport } from "./report.js";
import { initSettings } from "./settings.js";
import { clearHistory, loadDraft, loadHistory, saveCheck, saveDraft } from "./storage.js";

const claimInput = document.getElementById("claim");
const checkButton = document.getElementById("check-button");
const clearInputButton = document.getElementById("clear-input");
const characterCount = document.getElementById("character-count");
const status = document.getElementById("status");
const progress = document.getElementById("analysis-progress");
const progressMessage = document.getElementById("progress-message");
const recentCheck = document.getElementById("recent-check");
const restoreRecent = document.getElementById("restore-recent");
const reportSection = document.getElementById("report");
const progressMessages = ["Виділяємо перевірювані факти…", "Зіставляємо наявні докази…", "Агенти перевіряють висновки одне одного…", "Арбітр готує зрозуміле пояснення…"];
let progressTimer;

function updateInputState() {
  const length = claimInput.value.length;
  characterCount.textContent = `${length.toLocaleString("uk-UA")} / 10 000`;
  clearInputButton.hidden = length === 0;
}

function latestEntry() { return loadHistory()[0] || null; }

function refreshRecent(settings) {
  const latest = settings.rememberHistory ? latestEntry() : null;
  recentCheck.hidden = !latest;
  if (latest) restoreRecent.textContent = `Остання перевірка: ${latest.claim}`;
}

function restoreEntry(entry, scroll = true) {
  if (!entry) return;
  claimInput.value = entry.claim;
  updateInputState();
  renderReport(entry.report);
  status.textContent = "Відновлено останню перевірку з цього браузера.";
  if (scroll) reportSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

const getSettings = initSettings({
  onClearHistory: () => {
    clearHistory();
    recentCheck.hidden = true;
    status.textContent = "Локальну історію очищено.";
  },
  onSettingsChange: (settings) => {
    if (!settings.rememberHistory) saveDraft("");
    refreshRecent(settings);
  },
});

function setPending(isPending) {
  checkButton.disabled = isPending;
  claimInput.disabled = isPending;
  clearInputButton.disabled = isPending;
  progress.hidden = !isPending;
  if (!isPending) return window.clearInterval(progressTimer);
  let index = 0;
  progressMessage.textContent = progressMessages[index];
  progressTimer = window.setInterval(() => {
    index = (index + 1) % progressMessages.length;
    progressMessage.textContent = progressMessages[index];
  }, 2300);
}

async function checkClaim() {
  const claim = claimInput.value.trim();
  if (!claim) {
    status.textContent = "Введіть новину або твердження перед перевіркою.";
    return claimInput.focus();
  }
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 120_000);
  setPending(true);
  status.textContent = "Триває перевірка. Не закривайте сторінку.";
  try {
    const response = await fetch("/api/check", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ claim }), signal: controller.signal });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const report = await response.json();
    renderReport(report);
    if (getSettings().rememberHistory) {
      saveCheck(report);
      saveDraft(report.claim);
      refreshRecent(getSettings());
    }
    status.textContent = "Перевірку завершено. Результат наведено нижче.";
    reportSection.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    status.textContent = error.name === "AbortError" ? "Час очікування минув. Спробуйте ще раз." : "Не вдалося отримати результат. Перевірте роботу сервера.";
  } finally {
    window.clearTimeout(timeout);
    setPending(false);
  }
}

claimInput.addEventListener("input", () => {
  updateInputState();
  if (getSettings().rememberHistory) saveDraft(claimInput.value);
});
claimInput.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") checkClaim();
});
checkButton.addEventListener("click", checkClaim);
clearInputButton.addEventListener("click", () => {
  claimInput.value = "";
  saveDraft("");
  updateInputState();
  claimInput.focus();
});
restoreRecent.addEventListener("click", () => restoreEntry(latestEntry()));
document.getElementById("new-check-button").addEventListener("click", () => {
  claimInput.focus();
  claimInput.scrollIntoView({ behavior: "smooth", block: "center" });
});

const initialSettings = getSettings();
const latest = initialSettings.rememberHistory ? latestEntry() : null;
claimInput.value = (initialSettings.rememberHistory ? loadDraft() : "") || latest?.claim || "";
updateInputState();
refreshRecent(initialSettings);
if (latest) restoreEntry(latest, false);
document.documentElement.dataset.appReady = "true";
