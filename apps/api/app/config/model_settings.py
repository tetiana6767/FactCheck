"""Типізовані налаштування рольової маршрутизації моделей."""

from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

RoutingMode = Literal["role", "single"]
ExecutionMode = Literal["economy", "research"]
SearchEngine = Literal["exa", "parallel", "perplexity"]


class ModelRoutingSettings(BaseSettings):
    """Завантажити безпечну конфігурацію OpenRouter із середовища."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        env_prefix="OPENROUTER_",
        extra="ignore",
        frozen=True,
    )

    api_key: SecretStr | None = None
    endpoint: str = "https://openrouter.ai/api/v1/chat/completions"
    routing_mode: RoutingMode = "role"
    execution_mode: ExecutionMode = "economy"

    model_default: str = "openai/gpt-4o-mini"
    model_claim: str = "mistralai/mistral-small-3.2-24b-instruct"
    model_evidence: str = "deepseek/deepseek-v4.1-flash-20260910"
    model_source: str = "qwen/qwen3.5-9b"
    model_linguistic: str = "mistralai/mistral-small-3.2-24b-instruct"
    model_skeptic: str = "deepseek/deepseek-v4.1-flash-20260910"
    model_verifier: str = "openai/gpt-4o-mini"
    model_arbiter: str = "openai/gpt-4o-mini"
    model_fallback: str = "mistralai/mistral-small-3.2-24b-instruct"

    web_search_enabled: bool = True
    web_search_model: str = "openai/gpt-4o-mini"
    web_search_engine: SearchEngine = "parallel"
    web_search_mode: str = "basic"
    web_search_max_claims: int = Field(default=3, ge=1, le=10)
    web_search_max_results: int = Field(default=3, ge=1, le=10)
    web_search_max_uses: int = Field(default=2, ge=1, le=3)

    timeout_seconds: float = Field(default=30.0, gt=0, le=120)
    max_tokens: int = Field(default=1_200, ge=100, le=16_384)
    max_retries: int = Field(default=2, ge=0, le=5)
    max_report_cost_usd: float = Field(default=0.02, gt=0, le=1)
    max_input_price_per_million: float = Field(default=0.15, gt=0, le=1)
    max_output_price_per_million: float = Field(default=0.60, gt=0, le=2)

    @field_validator(
        "model_default",
        "model_claim",
        "model_evidence",
        "model_source",
        "model_linguistic",
        "model_skeptic",
        "model_verifier",
        "model_arbiter",
        "model_fallback",
        "web_search_model",
    )
    @classmethod
    def validate_model_id(cls, value: str) -> str:
        """Відхилити порожні або некваліфіковані model ID."""

        cleaned = value.strip()
        if "/" not in cleaned or cleaned.startswith("/") or cleaned.endswith("/"):
            raise ValueError("Model ID must use the provider/model format")
        return cleaned

    @property
    def enabled(self) -> bool:
        """Перевірити наявність непорожнього секретного ключа."""

        return bool(self.api_key and self.api_key.get_secret_value().strip())

    @property
    def web_search_ready(self) -> bool:
        """Увімкнути вебпошук лише за наявності ключа."""

        return self.enabled and self.web_search_enabled
