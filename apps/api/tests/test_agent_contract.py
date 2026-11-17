"""Тести контрактів агента й вимкненого режиму."""

import pytest
from pydantic import ValidationError

from app.schemas.agent import ClaimAssessment, SingleAgentAnalysis
from app.schemas.check import EvidenceSnapshot
from app.services.model_gateway import DisabledModelGateway, ModelContext


def test_agent_contract_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        SingleAgentAnalysis.model_validate(
            {
                "summary": "Аналіз",
                "linguistic_flags": [],
                "claim_assessments": [],
                "uncertainties": [],
                "confidence": 0.5,
                "high_risk": False,
                "unexpected": True,
            }
        )


def test_claim_assessment_rejects_unknown_status() -> None:
    with pytest.raises(ValidationError):
        ClaimAssessment(
            claim_id="claim-1",
            status="probably_true",
            rationale="Невідомий статус.",
            evidence_ids=(),
        )


def test_disabled_gateway_returns_safe_status() -> None:
    context = ModelContext(
        text="Київ — столиця України.",
        claims=(),
        evidence_snapshot=EvidenceSnapshot(),
    )

    result = DisabledModelGateway().analyze(context)

    assert result.analysis is None
    assert result.run.mode == "disabled"
    assert result.run.status == "not_configured"
    assert result.run.error_code == "openrouter_not_configured"
