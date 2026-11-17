"""Контракти мультиагентного звіту й інтегральної оцінки."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.graph.roles import AgentRole
from app.schemas.agent import ModelRun, SingleAgentAnalysis


class AgentRoleResult(BaseModel):
    """Результат і telemetry однієї спеціалізованої ролі."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    role: AgentRole
    analysis: SingleAgentAnalysis | None = None
    run: ModelRun


class IntegralAssessment(BaseModel):
    """Пояснювані складові сили наданих доказів."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    support: float = Field(ge=0, le=1)
    refutation: float = Field(ge=0, le=1)
    coverage: float = Field(ge=0, le=1)
    consensus: float = Field(ge=0, le=1)
    score: float = Field(ge=0, le=1)
    status: Literal["insufficient_evidence"] = "insufficient_evidence"


class MultiAgentReport(BaseModel):
    """Простежуваний підсумок виконання LangGraph."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    execution_mode: Literal["economy", "research"]
    role_results: tuple[AgentRoleResult, ...] = ()
    completed_roles: tuple[AgentRole, ...] = ()
    failed_roles: tuple[AgentRole, ...] = ()
    skipped_roles: tuple[AgentRole, ...] = ()
    integral: IntegralAssessment
    total_cost_usd: float = Field(default=0, ge=0)
