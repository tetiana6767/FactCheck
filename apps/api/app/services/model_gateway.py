"""Порт мовної моделі та безпечний вимкнений адаптер."""

from dataclasses import dataclass
from typing import Protocol

from app.schemas.agent import ModelResult, ModelRun
from app.schemas.check import Claim, EvidenceSnapshot


@dataclass(frozen=True)
class ModelContext:
    """Дані, дозволені для передавання мовній моделі."""

    text: str
    claims: tuple[Claim, ...]
    evidence_snapshot: EvidenceSnapshot


class ModelGateway(Protocol):
    """Виконати один структурований аналіз."""

    def analyze(self, context: ModelContext) -> ModelResult:
        """Повернути валідований результат і telemetry."""


class DisabledModelGateway:
    """Зберегти роботу застосунку без конфігурації OpenRouter."""

    def analyze(self, context: ModelContext) -> ModelResult:
        """Повернути явний статус вимкненого LLM-режиму."""

        del context
        return ModelResult(
            run=ModelRun(
                mode="disabled",
                status="not_configured",
                error_code="openrouter_not_configured",
            )
        )
