"""Виконання спеціалізованої ролі через модельний gateway."""

from app.graph.roles import AgentRole
from app.graph.runner import RoleExecutionError, RoleRunner, RoleRunResult
from app.graph.state import FactCheckGraphState
from app.schemas.multi_agent import AgentRoleResult
from app.services.model_gateway import ModelContext
from app.services.role_gateway_factory import RoleModelGatewayFactory


class GatewayRoleRunner(RoleRunner):
    """Перетворити результат OpenRouter на доменне оновлення графа."""

    def __init__(self, factory: RoleModelGatewayFactory) -> None:
        self._factory = factory

    def run(
        self, role: AgentRole, state: FactCheckGraphState
    ) -> RoleRunResult:
        """Виконати роль на спільному незмінному EvidenceSnapshot."""

        gateway = self._factory.build(role)
        result = gateway.analyze(
            ModelContext(
                text=state.text,
                claims=state.claims,
                evidence_snapshot=state.evidence_snapshot,
                prior_results=state.role_results,
            )
        )
        role_result = AgentRoleResult(
            role=role,
            analysis=result.analysis,
            run=result.run,
        )
        if result.run.status != "completed" or result.analysis is None:
            raise RoleExecutionError(role_result)

        statuses = tuple(
            assessment.status
            for assessment in result.analysis.claim_assessments
        )
        return RoleRunResult(
            role_result=role_result,
            preliminary_statuses=statuses,
            high_risk=result.analysis.high_risk,
        )
