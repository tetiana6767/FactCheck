const SETTINGS_KEY = "factcheck.settings.v1";
const HISTORY_KEY = "factcheck.history.v1";
const DRAFT_KEY = "factcheck.draft.v1";
const HISTORY_LIMIT = 3;

export const DEFAULT_SETTINGS = Object.freeze({
  theme: "system",
  fontSize: "standard",
  detail: "balanced",
  rememberHistory: true,
});

function readJson(key, fallback) {
  try {
    const value = window.localStorage.getItem(key);
    return value ? JSON.parse(value) : fallback;
  } catch {
    return fallback;
  }
}

function writeJson(key, value) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

export function loadSettings() {
  return { ...DEFAULT_SETTINGS, ...readJson(SETTINGS_KEY, {}) };
}

export function saveSettings(settings) {
  writeJson(SETTINGS_KEY, settings);
}

export function loadHistory() {
  const history = readJson(HISTORY_KEY, []);
  return Array.isArray(history) ? history : [];
}

export function saveCheck(report) {
  const entry = {
    id: `${Date.now()}`,
    checkedAt: new Date().toISOString(),
    claim: report.claim,
    report,
  };
  const history = loadHistory().filter((item) => item.claim !== report.claim);
  writeJson(HISTORY_KEY, [entry, ...history].slice(0, HISTORY_LIMIT));
  return entry;
}

export function clearHistory() {
  try {
    window.localStorage.removeItem(HISTORY_KEY);
    window.localStorage.removeItem(DRAFT_KEY);
  } catch {
    // Сторінка продовжує працювати, навіть якщо сховище заблоковане.
  }
}

export function loadDraft() {
  try {
    return window.localStorage.getItem(DRAFT_KEY) || "";
  } catch {
    return "";
  }
}

export function saveDraft(text) {
  try {
    if (text) window.localStorage.setItem(DRAFT_KEY, text);
    else window.localStorage.removeItem(DRAFT_KEY);
  } catch {
    // Чернетка є зручною функцією, але не блокує основну перевірку.
  }
}
