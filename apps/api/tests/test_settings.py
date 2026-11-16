"""Тести конфігурації OpenRouter."""

from app.settings import OpenRouterSettings


def test_settings_disable_model_without_environment(monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

    settings = OpenRouterSettings.from_env()

    assert settings.enabled is False
    assert settings.api_key is None
    assert settings.model is None


def test_settings_enable_model_with_key_and_model(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", " secret ")
    monkeypatch.setenv("OPENROUTER_MODEL", " provider/model ")

    settings = OpenRouterSettings.from_env()

    assert settings.enabled is True
    assert settings.api_key == "secret"
    assert settings.model == "provider/model"
