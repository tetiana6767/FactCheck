"""Контракти структурованого аналізу мовної моделі."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ClaimStatus = Literal[
    "supported",
    "refuted",
    "conflicting",
    "insufficient_evidence",
]
ModelMode = Literal["disabled", "mock", "openrouter"]
ModelStatus = Literal[
    "not_configured",
    "completed",
    "invalid_response",
    "timeout",
    "provider_error",
]


class LinguisticFlag(BaseModel):
    """Мовний сигнал без висновку про фактичну істинність."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: str
    fragment: str
    explanation: str


class ClaimAssessment(BaseModel):
    """Оцінка однієї тези лише за наданими доказами."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_id: str
    status: ClaimStatus
    rationale: str
    evidence_ids: tuple[str, ...]


class SingleAgentAnalysis(BaseModel):
    """Строга відповідь контрольного універсального агента."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    summary: str
    linguistic_flags: tuple[LinguisticFlag, ...]
    claim_assessments: tuple[ClaimAssessment, ...]
    uncertainties: tuple[str, ...]
    confidence: float = Field(ge=0, le=1)
    high_risk: bool


class ModelRun(BaseModel):
    """Безпечні метадані одного виклику мовної моделі."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: ModelMode
    model: str | None = None
    status: ModelStatus
    latency_ms: int | None = Field(default=None, ge=0)
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0)
    error_code: str | None = None


class ModelResult(BaseModel):
    """Результат адаптера разом із telemetry."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    analysis: SingleAgentAnalysis | None = None
    run: ModelRun
