"""Координація виділення тверджень і тестового пошуку."""

from app.schemas.check import CheckRequest, CheckResponse
from app.services.claim_extractor import ClaimExtractor
from app.services.evidence_ledger import EvidenceLedger
from app.services.linguistic_analyzer import LinguisticAnalyzer
from app.services.model_gateway import (
    DisabledModelGateway,
    ModelContext,
    ModelGateway,
)
from app.services.search_gateway import InMemorySearchGateway, SearchGateway


class CheckService:
    """Сформувати простежуваний звіт без зовнішньої мережі."""

    def __init__(
        self,
        extractor: ClaimExtractor | None = None,
        search_gateway: SearchGateway | None = None,
        model_gateway: ModelGateway | None = None,
        linguistic_analyzer: LinguisticAnalyzer | None = None,
    ) -> None:
        self._extractor = extractor or ClaimExtractor()
        self._search_gateway = search_gateway or InMemorySearchGateway()
        self._model_gateway = model_gateway or DisabledModelGateway()
        self._linguistic_analyzer = linguistic_analyzer or LinguisticAnalyzer()

    def analyze(self, request: CheckRequest) -> CheckResponse:
        """Виділити тези й повернути знімок тестових доказів."""

        claims = self._extractor.extract(request.claim)
        ledger = EvidenceLedger()
        for claim in claims:
            ledger.extend(self._search_gateway.search(claim))
        snapshot = ledger.snapshot()
        linguistic_flags = self._linguistic_analyzer.analyze(request.claim)
        model_result = self._model_gateway.analyze(
            ModelContext(
                text=request.claim,
                claims=claims,
                evidence_snapshot=snapshot,
            )
        )

        return CheckResponse(
            claim=request.claim,
            verdict="insufficient_evidence",
            explanation=self._build_explanation(len(claims), len(snapshot.items)),
            linguistic_flags=list(linguistic_flags),
            claims=list(claims),
            evidence=list(snapshot.items),
            evidence_snapshot=snapshot,
            agent_analysis=model_result.analysis,
            model_run=model_result.run,
        )

    @staticmethod
    def _build_explanation(claim_count: int, evidence_count: int) -> str:
        if claim_count == 0:
            return (
                "Перевірюваних тверджень за базовими правилами не виділено. "
                "Сформулюйте конкретну декларативну тезу."
            )
        return (
            f"Виділено тверджень: {claim_count}. Записів у локальному "
            f"тестовому корпусі: {evidence_count}. Тестовий корпус демонструє "
            "простежуваність, але не замінює перевірку зовнішніх джерел, тому "
            "доказів для фактологічного висновку недостатньо."
        )
