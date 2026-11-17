"""Конфігурація інтеграції OpenRouter зі змінних середовища."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class OpenRouterSettings:
    """Налаштування сервера без збереження секретів у коді."""

    api_key: str | None
    model: str | None
    endpoint: str = "https://openrouter.ai/api/v1/chat/completions"
    timeout_seconds: float = 30.0
    max_tokens: int = 1_200
    max_retries: int = 2
    retry_delay_seconds: float = 0.5
    fallback_models: tuple[str, ...] = ()
    max_input_price_per_million: float = 0.15
    max_output_price_per_million: float = 0.60

    @classmethod
    def from_env(cls) -> "OpenRouterSettings":
        """Прочитати й очистити значення конфігурації."""

        return cls(
            api_key=cls._clean(os.getenv("OPENROUTER_API_KEY")),
            model=cls._clean(os.getenv("OPENROUTER_MODEL")),
        )

    @property
    def enabled(self) -> bool:
        """Перевірити готовність обов'язкових параметрів."""

        return self.api_key is not None and self.model is not None

    @staticmethod
    def _clean(value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None
