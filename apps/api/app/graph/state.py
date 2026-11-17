"""Незмінний стан майбутнього LangGraph-процесу."""

from pydantic import BaseModel, ConfigDict

from app.graph.roles import AgentRole
from app.schemas.agent import ClaimStatus, LinguisticFlag
from app.schemas.check import Claim, EvidenceSnapshot
from app.schemas.multi_agent import AgentRoleResult


class FactCheckGraphState(BaseModel):
    """Спільні дані агентів для одного звіту."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str
    claims: tuple[Claim, ...] = ()
    evidence_snapshot: EvidenceSnapshot = EvidenceSnapshot()
    linguistic_flags: tuple[LinguisticFlag, ...] = ()
    preliminary_statuses: tuple[ClaimStatus, ...] = ()
    completed_roles: tuple[AgentRole, ...] = ()
    failed_roles: tuple[AgentRole, ...] = ()
    skipped_roles: tuple[AgentRole, ...] = ()
    role_results: tuple[AgentRoleResult, ...] = ()
    high_risk: bool = False

    @property
    def has_conflict(self) -> bool:
        """Виявити явну або міжагентну суперечність."""

        statuses = set(self.preliminary_statuses)
        return "conflicting" in statuses or {
            "supported",
            "refuted",
        }.issubset(statuses)

    def with_completed_role(self, role: AgentRole) -> "FactCheckGraphState":
        """Повернути новий стан без мутації початкового."""

        if role in self.completed_roles:
            return self
        return self.model_copy(
            update={"completed_roles": (*self.completed_roles, role)}
        )
