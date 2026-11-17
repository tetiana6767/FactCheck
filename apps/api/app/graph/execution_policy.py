"""Економна політика умовного запуску агентів."""

from app.config.model_settings import ExecutionMode
from app.graph.roles import AgentRole
from app.graph.state import FactCheckGraphState


class RoleExecutionPolicy:
    """Вирішити, чи виправданий модельний виклик для ролі."""

    def __init__(
        self,
        mode: ExecutionMode = "economy",
        max_cost_usd: float | None = None,
    ) -> None:
        self._mode = mode
        self._max_cost_usd = max_cost_usd

    def should_run(self, role: AgentRole, state: FactCheckGraphState) -> bool:
        """Застосувати умови економії або повного експерименту."""

        if not state.claims:
            return False
        if self._budget_exhausted(state):
            return False
        if self._mode == "research":
            return self._research_decision(role, state)
        return self._economy_decision(role, state)

    def _budget_exhausted(self, state: FactCheckGraphState) -> bool:
        """Зупинити нові виклики після досягнення бюджету звіту."""

        if self._max_cost_usd is None:
            return False
        spent = sum(
            result.run.cost_usd or 0 for result in state.role_results
        )
        return spent >= self._max_cost_usd

    @staticmethod
    def _research_decision(
        role: AgentRole, state: FactCheckGraphState
    ) -> bool:
        if role == AgentRole.ARBITER:
            return bool(state.completed_roles)
        return True

    @staticmethod
    def _economy_decision(
        role: AgentRole, state: FactCheckGraphState
    ) -> bool:
        if role == AgentRole.CLAIM:
            return True
        if role in {AgentRole.EVIDENCE, AgentRole.SOURCE}:
            return bool(state.evidence_snapshot.items)
        if role == AgentRole.LINGUISTIC:
            return bool(state.linguistic_flags)
        if role == AgentRole.SKEPTIC:
            decisive = {"supported", "refuted", "conflicting"}
            return bool(decisive.intersection(state.preliminary_statuses))
        if role == AgentRole.VERIFIER:
            return state.has_conflict or state.high_risk
        if role == AgentRole.ARBITER:
            return bool(state.completed_roles)
        return False
