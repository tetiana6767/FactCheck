"""Контракти запиту й відповіді перевірки."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.schemas.agent import (
    ClaimStatus,
    LinguisticFlag,
    ModelRun,
    SingleAgentAnalysis,
)
from app.schemas.multi_agent import MultiAgentReport

ClaimText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=10_000),
]


class CheckRequest(BaseModel):
    """Запит на перевірку одного твердження або новини."""

    model_config = ConfigDict(extra="forbid")

    claim: ClaimText


class Claim(BaseModel):
    """Перевірюване твердження з позицією у вхідному тексті."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    text: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)


class Evidence(BaseModel):
    """Посилання на доказ, пов'язаний із твердженням."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    claim_id: str
    title: str
    url: str
    quote: str | None = None
    source_date: str | None = None
    source_type: Literal["test_corpus", "web"]


class EvidenceSnapshot(BaseModel):
    """Незмінний знімок доказів для одного запуску перевірки."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal[1] = 1
    items: tuple[Evidence, ...] = ()


class CheckResponse(BaseModel):
    """Структурований звіт із твердженнями й тестовими доказами."""

    claim: str
    verdict: ClaimStatus
    explanation: str
    linguistic_flags: list[LinguisticFlag] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    evidence_snapshot: EvidenceSnapshot = Field(default_factory=EvidenceSnapshot)
    agent_analysis: SingleAgentAnalysis | None = None
    multi_agent_report: MultiAgentReport | None = None
    model_run: ModelRun = Field(
        default_factory=lambda: ModelRun(
            mode="disabled",
            status="not_configured",
            error_code="openrouter_not_configured",
        )
    )


class HealthResponse(BaseModel):
    """Стан готовності HTTP API."""

    status: Literal["ok"]
