"""Координація виділення тверджень і тестового пошуку."""

from app.schemas.check import CheckRequest, CheckResponse
from app.services.claim_extractor import ClaimExtractor
from app.services.evidence_ledger import EvidenceLedger
from app.services.search_gateway import InMemorySearchGateway, SearchGateway


class CheckService:
    """Сформувати простежуваний звіт без зовнішньої мережі."""

    def __init__(
        self,
        extractor: ClaimExtractor | None = None,
        search_gateway: SearchGateway | None = None,
    ) -> None:
        self._extractor = extractor or ClaimExtractor()
        self._search_gateway = search_gateway or InMemorySearchGateway()

    def analyze(self, request: CheckRequest) -> CheckResponse:
        """Виділити тези й повернути знімок тестових доказів."""

        claims = self._extractor.extract(request.claim)
        ledger = EvidenceLedger()
        for claim in claims:
            ledger.extend(self._search_gateway.search(claim))
        snapshot = ledger.snapshot()

        return CheckResponse(
            claim=request.claim,
            verdict="insufficient_evidence",
            explanation=self._build_explanation(len(claims), len(snapshot.items)),
            claims=list(claims),
            evidence=list(snapshot.items),
            evidence_snapshot=snapshot,
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
