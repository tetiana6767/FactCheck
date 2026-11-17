"""Тести незмінного стану й економної політики графа."""

from app.graph.execution_policy import RoleExecutionPolicy
from app.graph.roles import AgentRole
from app.graph.state import FactCheckGraphState
from app.schemas.agent import LinguisticFlag
from app.schemas.agent import ModelRun
from app.schemas.check import Claim, Evidence, EvidenceSnapshot
from app.schemas.multi_agent import AgentRoleResult


def _claim() -> Claim:
    return Claim(id="claim-1", text="Теза.", start=0, end=5)


def _evidence_snapshot() -> EvidenceSnapshot:
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


def test_economy_mode_skips_roles_without_required_data() -> None:
    state = FactCheckGraphState(text="Теза.", claims=(_claim(),))
    policy = RoleExecutionPolicy("economy")

    assert policy.should_run(AgentRole.CLAIM, state) is True
    assert policy.should_run(AgentRole.EVIDENCE, state) is False
    assert policy.should_run(AgentRole.LINGUISTIC, state) is False
    assert policy.should_run(AgentRole.VERIFIER, state) is False


def test_economy_mode_runs_only_justified_control_roles() -> None:
    state = FactCheckGraphState(
        text="Теза.",
        claims=(_claim(),),
        evidence_snapshot=_evidence_snapshot(),
        preliminary_statuses=("supported", "refuted"),
        completed_roles=(AgentRole.CLAIM, AgentRole.EVIDENCE),
    )
    policy = RoleExecutionPolicy("economy")

    assert policy.should_run(AgentRole.SOURCE, state) is True
    assert policy.should_run(AgentRole.SKEPTIC, state) is True
    assert policy.should_run(AgentRole.VERIFIER, state) is True
    assert policy.should_run(AgentRole.ARBITER, state) is True


def test_linguistic_agent_runs_only_after_local_signal() -> None:
    flag = LinguisticFlag(
        kind="sensational_phrase",
        fragment="шок",
        explanation="Сенсаційна лексика.",
    )
    state = FactCheckGraphState(
        text="Шок.",
        claims=(_claim(),),
        linguistic_flags=(flag,),
    )

    assert RoleExecutionPolicy().should_run(AgentRole.LINGUISTIC, state) is True


def test_research_mode_runs_all_non_final_roles() -> None:
    state = FactCheckGraphState(text="Теза.", claims=(_claim(),))
    policy = RoleExecutionPolicy("research")

    roles = set(AgentRole) - {AgentRole.ARBITER}
    assert all(policy.should_run(role, state) for role in roles)
    assert policy.should_run(AgentRole.ARBITER, state) is False


def test_state_update_is_immutable_and_idempotent() -> None:
    initial = FactCheckGraphState(text="Теза.", claims=(_claim(),))

    updated = initial.with_completed_role(AgentRole.CLAIM)
    repeated = updated.with_completed_role(AgentRole.CLAIM)

    assert initial.completed_roles == ()
    assert updated.completed_roles == (AgentRole.CLAIM,)
    assert repeated is updated


def test_policy_stops_new_roles_after_report_budget_is_spent() -> None:
    state = FactCheckGraphState(
        text="Теза.",
        claims=(_claim(),),
        role_results=(
            AgentRoleResult(
                role=AgentRole.CLAIM,
                run=ModelRun(
                    mode="mock",
                    status="completed",
                    cost_usd=0.02,
                ),
            ),
        ),
    )

    policy = RoleExecutionPolicy("research", max_cost_usd=0.02)

    assert policy.should_run(AgentRole.EVIDENCE, state) is False
