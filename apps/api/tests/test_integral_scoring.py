"""Тести пояснюваної інтегральної оцінки."""

from app.graph.roles import AgentRole
from app.graph.state import FactCheckGraphState
from app.schemas.agent import (
    ClaimAssessment,
    ModelRun,
    SingleAgentAnalysis,
)
from app.schemas.check import Claim, Evidence, EvidenceSnapshot
from app.schemas.multi_agent import AgentRoleResult
from app.services.integral_scoring import IntegralScoreCalculator
from app.services.multi_agent_report import MultiAgentReportBuilder


def _analysis(status: str) -> SingleAgentAnalysis:
    return SingleAgentAnalysis(
        summary="Оцінка.",
        linguistic_flags=(),
        claim_assessments=(
            ClaimAssessment(
                claim_id="claim-1",
                status=status,
                rationale="Тест.",
                evidence_ids=("evidence-1",),
            ),
        ),
        uncertainties=(),
        confidence=0.7,
        high_risk=False,
    )


def _state() -> FactCheckGraphState:
    claim = Claim(id="claim-1", text="Теза.", start=0, end=5)
    evidence = Evidence(
        id="evidence-1",
        claim_id="claim-1",
        title="Джерело",
        url="urn:factcheck:test-corpus:source",
        quote="Цитата",
        source_type="test_corpus",
    )
    results = (
        AgentRoleResult(
            role=AgentRole.EVIDENCE,
            analysis=_analysis("supported"),
            run=ModelRun(mode="mock", status="completed", cost_usd=0.001),
        ),
        AgentRoleResult(
            role=AgentRole.SKEPTIC,
            analysis=_analysis("refuted"),
            run=ModelRun(mode="mock", status="completed", cost_usd=0.002),
        ),
    )
    return FactCheckGraphState(
        text="Теза.",
        claims=(claim,),
        evidence_snapshot=EvidenceSnapshot(items=(evidence,)),
        role_results=results,
    )


def test_integral_score_exposes_conflicting_components() -> None:
    integral = IntegralScoreCalculator().calculate(_state())

    assert integral.support == 0.5
    assert integral.refutation == 0.5
    assert integral.coverage == 1
    assert integral.consensus == 0.5
    assert integral.score == 0.25
    assert integral.status == "insufficient_evidence"


def test_report_sums_actual_role_costs() -> None:
    report = MultiAgentReportBuilder().build(_state(), "research")

    assert report.total_cost_usd == 0.003
    assert report.execution_mode == "research"
