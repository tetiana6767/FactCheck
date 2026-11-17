"""Інтеграційний тест CheckService та локального LangGraph."""

from app.graph.roles import AgentRole
from app.graph.runner import RoleRunResult
from app.graph.workflow import FactCheckWorkflow
from app.schemas.agent import (
    ClaimAssessment,
    ModelRun,
    SingleAgentAnalysis,
)
from app.schemas.check import CheckRequest
from app.schemas.multi_agent import AgentRoleResult
from app.services.check_service import CheckService


class SuccessfulRoleRunner:
    def run(self, role, state) -> RoleRunResult:
        assessments = tuple(
            ClaimAssessment(
                claim_id=claim.id,
                status="insufficient_evidence",
                rationale="Зовнішніх доказів немає.",
                evidence_ids=(),
            )
            for claim in state.claims
        )
        analysis = SingleAgentAnalysis(
            summary=f"Роль {role.value} завершена.",
            linguistic_flags=(),
            claim_assessments=assessments,
            uncertainties=("Потрібні зовнішні джерела.",),
            confidence=0.2,
            high_risk=False,
        )
        role_result = AgentRoleResult(
            role=role,
            analysis=analysis,
            run=ModelRun(
                mode="mock",
                model=f"test/{role.value}",
                status="completed",
                cost_usd=0.0001,
            ),
        )
        return RoleRunResult(
            role_result=role_result,
            preliminary_statuses=("insufficient_evidence",),
        )


def test_check_service_returns_multi_agent_report() -> None:
    workflow = FactCheckWorkflow(SuccessfulRoleRunner())
    service = CheckService(workflow=workflow)

    response = service.analyze(CheckRequest(claim="Нова перевірювана теза."))

    assert response.verdict == "insufficient_evidence"
    assert response.multi_agent_report is not None
    assert response.multi_agent_report.completed_roles == (
        AgentRole.CLAIM,
        AgentRole.ARBITER,
    )
    assert response.multi_agent_report.total_cost_usd == 0.0002
    assert response.agent_analysis is not None
    assert response.model_run.model == "test/arbiter"
