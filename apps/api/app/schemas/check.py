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


class Evidence(BaseModel):
    """Посилання на доказ, пов'язаний із твердженням."""

    model_config = ConfigDict(extra="forbid")

    title: str
    url: str
    quote: str | None = None


class CheckResponse(BaseModel):
    """Структурований звіт першого етапу."""

    claim: str
    verdict: Literal["insufficient_evidence"]
    explanation: str
    linguistic_flags: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Стан готовності HTTP API."""

    status: Literal["ok"]
