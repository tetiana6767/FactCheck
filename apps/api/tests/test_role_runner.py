"""Тести перетворення модельного результату на результат ролі."""

import pytest

from app.graph.roles import AgentRole
from app.graph.runner import RoleExecutionError
from app.graph.state import FactCheckGraphState
from app.schemas.agent import (
    ClaimAssessment,
    ModelResult,
    ModelRun,
    SingleAgentAnalysis,
)
from app.schemas.check import Claim
from app.services.role_runner import GatewayRoleRunner


class FakeGateway:
    def __init__(self, result: ModelResult) -> None:
        self._result = result

    def analyze(self, context):
        del context
        return self._result


class FakeFactory:
    def __init__(self, result: ModelResult) -> None:
        self._result = result

    def build(self, role: AgentRole) -> FakeGateway:
        del role
        return FakeGateway(self._result)


def _state() -> FactCheckGraphState:
    claim = Claim(id="claim-1", text="Теза.", start=0, end=5)
    return FactCheckGraphState(text="Теза.", claims=(claim,))


def _analysis() -> SingleAgentAnalysis:
    return SingleAgentAnalysis(
        summary="Доказів недостатньо.",
        linguistic_flags=(),
        claim_assessments=(
            ClaimAssessment(
                claim_id="claim-1",
                status="insufficient_evidence",
                rationale="Немає доказів.",
                evidence_ids=(),
            ),
        ),
        uncertainties=("Потрібні зовнішні джерела.",),
        confidence=0.2,
        high_risk=False,
    )


def test_role_runner_maps_validated_analysis() -> None:
    result = ModelResult(
        analysis=_analysis(),
        run=ModelRun(mode="mock", status="completed"),
    )
    runner = GatewayRoleRunner(FakeFactory(result))

    role_result = runner.run(AgentRole.CLAIM, _state())

    assert role_result.role_result.role == AgentRole.CLAIM
    assert role_result.preliminary_statuses == ("insufficient_evidence",)
    assert role_result.high_risk is False


def test_role_runner_preserves_controlled_provider_failure() -> None:
    result = ModelResult(
        run=ModelRun(
            mode="mock",
            status="timeout",
            error_code="openrouter_timeout",
        )
    )
    runner = GatewayRoleRunner(FakeFactory(result))

    with pytest.raises(RoleExecutionError) as captured:
        runner.run(AgentRole.EVIDENCE, _state())

    assert captured.value.role_result.role == AgentRole.EVIDENCE
    assert captured.value.role_result.run.error_code == "openrouter_timeout"
