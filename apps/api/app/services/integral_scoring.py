"""Пояснювана інтегральна оцінка сили наданих доказів."""

from collections import Counter

from app.graph.state import FactCheckGraphState
from app.schemas.multi_agent import IntegralAssessment


class IntegralScoreCalculator:
    """Обчислити покриття, консенсус і напрям оцінок агентів."""

    def calculate(self, state: FactCheckGraphState) -> IntegralAssessment:
        """Повернути консервативну оцінку без фактичного вердикту."""

        assessments = [
            assessment
            for result in state.role_results
            if result.analysis is not None
            for assessment in result.analysis.claim_assessments
        ]
        if not assessments:
            return IntegralAssessment(
                support=0,
                refutation=0,
                coverage=0,
                consensus=0,
                score=0,
                trust_score=0,
                risk_score=1,
            )

        counts = Counter(assessment.status for assessment in assessments)
        total = len(assessments)
        support = counts["supported"] / total
        refutation = counts["refuted"] / total
        consensus = max(counts.values()) / total

        valid_ids = {item.id for item in state.evidence_snapshot.items}
        covered_claims = {
            assessment.claim_id
            for assessment in assessments
            if valid_ids.intersection(assessment.evidence_ids)
        }
        coverage = (
            len(covered_claims) / len(state.claims) if state.claims else 0
        )
        directional_strength = max(support, refutation)
        score = coverage * consensus * directional_strength
        trust_score = coverage * consensus * support
        risk_score = 1 - trust_score
        status = self._resolve_status(
            support=support,
            refutation=refutation,
            coverage=coverage,
        )
        return IntegralAssessment(
            support=round(support, 4),
            refutation=round(refutation, 4),
            coverage=round(coverage, 4),
            consensus=round(consensus, 4),
            score=round(score, 4),
            trust_score=round(trust_score, 4),
            risk_score=round(risk_score, 4),
            status=status,
        )

    @staticmethod
    def _resolve_status(
        support: float, refutation: float, coverage: float
    ) -> str:
        """Визначити обережний статус лише за достатнього покриття."""

        if coverage < 0.5:
            return "insufficient_evidence"
        if support >= 0.6 and support > refutation:
            return "supported"
        if refutation >= 0.6 and refutation > support:
            return "refuted"
        if support > 0 and refutation > 0:
            return "conflicting"
        return "insufficient_evidence"
