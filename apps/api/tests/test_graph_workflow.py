"""Ізольовані тести LangGraph без модельної мережі."""

from app.graph.execution_policy import RoleExecutionPolicy
from app.graph.roles import AgentRole
from app.graph.runner import RoleExecutionError, RoleRunResult
from app.graph.state import FactCheckGraphState
from app.graph.workflow import FactCheckWorkflow
from app.schemas.agent import LinguisticFlag, ModelRun
from app.schemas.check import Claim, Evidence, EvidenceSnapshot
from app.schemas.multi_agent import AgentRoleResult


class FakeRoleRunner:
    """Зафіксувати порядок ролей і контрольовані результати."""

    def __init__(self, failing_role: AgentRole | None = None) -> None:
        self.calls: list[AgentRole] = []
        self.failing_role = failing_role

    def run(
        self, role: AgentRole, state: FactCheckGraphState
    ) -> RoleRunResult:
        del state
        self.calls.append(role)
        if role == self.failing_role:
            raise RoleExecutionError(
                AgentRoleResult(
                    role=role,
                    run=ModelRun(
                        mode="mock",
                        status="provider_error",
                        error_code="controlled_test_failure",
                    ),
                )
            )
        return RoleRunResult(
            role_result=AgentRoleResult(
                role=role,
                run=ModelRun(mode="mock", status="completed"),
            )
        )


def _claim() -> Claim:
    return Claim(id="claim-1", text="Теза.", start=0, end=5)


def _snapshot() -> EvidenceSnapshot:
    return EvidenceSnapshot(
        items=(
            Evidence(
                id="evidence-1",
                claim_id="claim-1",
                title="Джерело",
                url="urn:factcheck:test-corpus:source",
                quote="Цитата",
                source_type="test_corpus",
            ),
        )
    )


def test_economy_workflow_calls_only_claim_and_arbiter_without_evidence() -> None:
    runner = FakeRoleRunner()
    workflow = FactCheckWorkflow(runner)
    state = FactCheckGraphState(text="Теза.", claims=(_claim(),))

    result = workflow.invoke(state)

    assert runner.calls == [AgentRole.CLAIM, AgentRole.ARBITER]
    assert result.completed_roles == (AgentRole.CLAIM, AgentRole.ARBITER)
    assert set(result.skipped_roles) == {
        AgentRole.EVIDENCE,
        AgentRole.SOURCE,
        AgentRole.LINGUISTIC,
        AgentRole.SKEPTIC,
        AgentRole.VERIFIER,
    }


def test_research_workflow_calls_every_role() -> None:
    runner = FakeRoleRunner()
    workflow = FactCheckWorkflow(runner, RoleExecutionPolicy("research"))
    state = FactCheckGraphState(text="Теза.", claims=(_claim(),))

    result = workflow.invoke(state)

    assert runner.calls == list(AgentRole)
    assert result.completed_roles == tuple(AgentRole)
    assert result.skipped_roles == ()


def test_workflow_continues_after_partial_failure() -> None:
    runner = FakeRoleRunner(failing_role=AgentRole.EVIDENCE)
    flag = LinguisticFlag(
        kind="sensational_phrase",
        fragment="шок",
        explanation="Сенсаційна лексика.",
    )
    state = FactCheckGraphState(
        text="Шок. Теза.",
        claims=(_claim(),),
        evidence_snapshot=_snapshot(),
        linguistic_flags=(flag,),
        preliminary_statuses=("conflicting",),
    )

    result = FactCheckWorkflow(runner).invoke(state)

    assert AgentRole.EVIDENCE in result.failed_roles
    assert AgentRole.SOURCE in result.completed_roles
    assert AgentRole.VERIFIER in result.completed_roles
    assert AgentRole.ARBITER in result.completed_roles


def test_workflow_skips_all_roles_without_claims() -> None:
    runner = FakeRoleRunner()

    result = FactCheckWorkflow(runner).invoke(FactCheckGraphState(text="Думка."))

    assert runner.calls == []
    assert result.completed_roles == ()
    assert result.skipped_roles == tuple(AgentRole)
