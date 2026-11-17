"""Побудова API-звіту з фінального стану мультиагентного графа."""

from app.config.model_settings import ExecutionMode
from app.graph.state import FactCheckGraphState
from app.schemas.multi_agent import MultiAgentReport
from app.services.integral_scoring import IntegralScoreCalculator


class MultiAgentReportBuilder:
    """Зібрати telemetry, ролі й інтегральну оцінку."""

    def __init__(
        self, calculator: IntegralScoreCalculator | None = None
    ) -> None:
        self._calculator = calculator or IntegralScoreCalculator()

    def build(
        self, state: FactCheckGraphState, mode: ExecutionMode
    ) -> MultiAgentReport:
        """Повернути незмінний простежуваний звіт."""

        total_cost = sum(
            result.run.cost_usd or 0 for result in state.role_results
        )
        return MultiAgentReport(
            execution_mode=mode,
            role_results=state.role_results,
            completed_roles=state.completed_roles,
            failed_roles=state.failed_roles,
            skipped_roles=state.skipped_roles,
            integral=self._calculator.calculate(state),
            total_cost_usd=round(total_cost, 8),
        )
