"""Контракти запиту й відповіді перевірки."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

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
    source_type: Literal["test_corpus"]


class EvidenceSnapshot(BaseModel):
    """Незмінний знімок доказів для одного запуску перевірки."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal[1] = 1
    items: tuple[Evidence, ...] = ()


class CheckResponse(BaseModel):
    """Структурований звіт із твердженнями й тестовими доказами."""

    claim: str
    verdict: Literal["insufficient_evidence"]
    explanation: str
    linguistic_flags: list[str] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    evidence_snapshot: EvidenceSnapshot = Field(default_factory=EvidenceSnapshot)


class HealthResponse(BaseModel):
    """Стан готовності HTTP API."""

    status: Literal["ok"]
