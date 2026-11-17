"""Координація виділення тверджень і тестового пошуку."""

from app.config.model_settings import ExecutionMode
from app.graph.roles import AgentRole
from app.graph.state import FactCheckGraphState
from app.graph.workflow import FactCheckWorkflow
from app.schemas.agent import LinguisticFlag, ModelResult, ModelRun
from app.schemas.check import (
    CheckRequest,
    CheckResponse,
    Claim,
    EvidenceSnapshot,
)
from app.schemas.multi_agent import MultiAgentReport
from app.services.claim_extractor import ClaimExtractor
from app.services.evidence_ledger import EvidenceLedger
from app.services.linguistic_analyzer import LinguisticAnalyzer
from app.services.model_gateway import (
    DisabledModelGateway,
    ModelContext,
    ModelGateway,
)
from app.services.multi_agent_report import MultiAgentReportBuilder
from app.services.search_gateway import InMemorySearchGateway, SearchGateway


class CheckService:
    """Сформувати простежуваний звіт без зовнішньої мережі."""

    def __init__(
        self,
        extractor: ClaimExtractor | None = None,
        search_gateway: SearchGateway | None = None,
        model_gateway: ModelGateway | None = None,
        linguistic_analyzer: LinguisticAnalyzer | None = None,
        workflow: FactCheckWorkflow | None = None,
        execution_mode: ExecutionMode = "economy",
        report_builder: MultiAgentReportBuilder | None = None,
    ) -> None:
        self._extractor = extractor or ClaimExtractor()
        self._search_gateway = search_gateway or InMemorySearchGateway()
        self._model_gateway = model_gateway or DisabledModelGateway()
        self._linguistic_analyzer = linguistic_analyzer or LinguisticAnalyzer()
        self._workflow = workflow
        self._execution_mode = execution_mode
        self._report_builder = report_builder or MultiAgentReportBuilder()

    def analyze(self, request: CheckRequest) -> CheckResponse:
        """Виділити тези й повернути знімок тестових доказів."""

        claims = self._extractor.extract(request.claim)
        ledger = EvidenceLedger()
        for claim in claims:
            ledger.extend(self._search_gateway.search(claim))
        snapshot = ledger.snapshot()
        linguistic_flags = self._linguistic_analyzer.analyze(request.claim)
        model_result, multi_agent_report = self._run_models(
            request.claim,
            claims,
            snapshot,
            linguistic_flags,
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
            multi_agent_report=multi_agent_report,
            model_run=model_result.run,
        )

    def _run_models(
        self,
        text: str,
        claims: tuple[Claim, ...],
        snapshot: EvidenceSnapshot,
        linguistic_flags: tuple[LinguisticFlag, ...],
    ) -> tuple[ModelResult, MultiAgentReport | None]:
        if self._workflow is None:
            result = self._model_gateway.analyze(
                ModelContext(
                    text=text,
                    claims=claims,
                    evidence_snapshot=snapshot,
                )
            )
            return result, None

        final_state = self._workflow.invoke(
            FactCheckGraphState(
                text=text,
                claims=claims,
                evidence_snapshot=snapshot,
                linguistic_flags=linguistic_flags,
            )
        )
        report = self._report_builder.build(
            final_state, self._execution_mode
        )
        preferred = next(
            (
                result
                for result in reversed(final_state.role_results)
                if result.role == AgentRole.ARBITER
            ),
            None,
        )
        if preferred is None:
            return ModelResult(
                run=ModelRun(
                    mode="disabled",
                    status="not_configured",
                    error_code="arbiter_not_completed",
                )
            ), report
        return ModelResult(
            analysis=preferred.analysis,
            run=preferred.run,
        ), report

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
