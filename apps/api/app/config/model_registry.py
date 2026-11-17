"""Реєстр економних моделей для спеціалізованих агентів."""

from dataclasses import dataclass
from typing import Literal

from app.config.model_settings import ModelRoutingSettings
from app.graph.roles import AgentRole

Complexity = Literal["low", "medium", "high"]
Frequency = Literal["always", "frequent", "conditional"]


@dataclass(frozen=True)
class ModelRate:
    """Орієнтовна ціна в доларах за мільйон токенів."""

    input_per_million: float
    output_per_million: float

    def estimate(self, input_tokens: int, output_tokens: int) -> float:
        """Оцінити вартість без урахування кешу й знижок."""

        return (
            input_tokens * self.input_per_million
            + output_tokens * self.output_per_million
        ) / 1_000_000


@dataclass(frozen=True)
class ModelProfile:
    """Модель і ліміти однієї агентної ролі."""

    role: AgentRole
    model_id: str
    fallback_model: str | None
    complexity: Complexity
    frequency: Frequency
    max_tokens: int
    rate: ModelRate | None


MODEL_RATES = {
    "openai/gpt-4o-mini": ModelRate(0.15, 0.60),
    "deepseek/deepseek-v4.1-flash-20260910": ModelRate(0.006, 0.50),
    "qwen/qwen3.5-9b": ModelRate(0.08, 0.13),
    "mistralai/mistral-small-3.2-24b-instruct": ModelRate(0.075, 0.20),
}
GPT_4O_MINI_RATE = MODEL_RATES["openai/gpt-4o-mini"]

ROLE_POLICY = {
    AgentRole.CLAIM: ("medium", "always", 600),
    AgentRole.EVIDENCE: ("high", "frequent", 1_000),
    AgentRole.SOURCE: ("medium", "conditional", 500),
    AgentRole.LINGUISTIC: ("medium", "conditional", 400),
    AgentRole.SKEPTIC: ("high", "conditional", 900),
    AgentRole.VERIFIER: ("high", "conditional", 900),
    AgentRole.ARBITER: ("high", "always", 800),
}


class ModelRegistry:
    """Вибрати модель за роллю або єдиним режимом."""

    def __init__(self, settings: ModelRoutingSettings) -> None:
        self._settings = settings

    def profile(self, role: AgentRole) -> ModelProfile:
        """Повернути економний профіль для агентної ролі."""

        model_id = (
            self._settings.model_default
            if self._settings.routing_mode == "single"
            else self._role_models()[role]
        )
        complexity, frequency, role_limit = ROLE_POLICY[role]
        fallback = self._settings.model_fallback
        if fallback == model_id:
            fallback = None
        return ModelProfile(
            role=role,
            model_id=model_id,
            fallback_model=fallback,
            complexity=complexity,
            frequency=frequency,
            max_tokens=min(role_limit, self._settings.max_tokens),
            rate=MODEL_RATES.get(model_id),
        )

    def all_profiles(self) -> tuple[ModelProfile, ...]:
        """Повернути профілі в стабільному порядку графа."""

        return tuple(self.profile(role) for role in AgentRole)

    def default_models_fit_price_ceiling(self) -> bool:
        """Перевірити верхню межу ціни GPT-4o-mini."""

        rates = (profile.rate for profile in self.all_profiles())
        return all(
            rate is not None
            and rate.input_per_million <= GPT_4O_MINI_RATE.input_per_million
            and rate.output_per_million <= GPT_4O_MINI_RATE.output_per_million
            for rate in rates
        )

    def _role_models(self) -> dict[AgentRole, str]:
        return {
            AgentRole.CLAIM: self._settings.model_claim,
            AgentRole.EVIDENCE: self._settings.model_evidence,
            AgentRole.SOURCE: self._settings.model_source,
            AgentRole.LINGUISTIC: self._settings.model_linguistic,
            AgentRole.SKEPTIC: self._settings.model_skeptic,
            AgentRole.VERIFIER: self._settings.model_verifier,
            AgentRole.ARBITER: self._settings.model_arbiter,
        }
