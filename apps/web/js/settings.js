import { loadSettings, saveSettings } from "./storage.js";

function applySettings(settings) {
  const root = document.documentElement;
  root.dataset.theme = settings.theme;
  root.dataset.fontSize = settings.fontSize;
  root.dataset.detail = settings.detail;
}

function syncControls(dialog, settings) {
  ["theme", "fontSize", "detail"].forEach((name) => {
    const control = dialog.querySelector(`[name="${name}"][value="${settings[name]}"]`);
    if (control) control.checked = true;
  });
  dialog.querySelector("#remember-history").checked = settings.rememberHistory;
}

function readControls(dialog) {
  const form = new FormData(dialog.querySelector("form"));
  return {
    theme: form.get("theme") || "system",
    fontSize: form.get("fontSize") || "standard",
    detail: form.get("detail") || "balanced",
    rememberHistory: dialog.querySelector("#remember-history").checked,
  };
}

export function initSettings({ onClearHistory, onSettingsChange }) {
  const dialog = document.getElementById("settings-dialog");
  const clearButton = document.getElementById("clear-history");
  let settings = loadSettings();
  applySettings(settings);
  syncControls(dialog, settings);

  document.getElementById("settings-button").addEventListener("click", () => dialog.showModal());
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
  dialog.addEventListener("change", () => {
    settings = readControls(dialog);
    saveSettings(settings);
    applySettings(settings);
    onSettingsChange(settings);
  });
  clearButton.addEventListener("click", () => {
    onClearHistory();
    clearButton.textContent = "Історію очищено";
    window.setTimeout(() => {
      clearButton.textContent = "Очистити локальну історію";
    }, 1800);
  });
  return () => ({ ...settings });
}
