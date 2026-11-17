"""Композиція мультиагентного workflow з конфігурації."""

from app.config.model_settings import ModelRoutingSettings
from app.graph.execution_policy import RoleExecutionPolicy
from app.graph.workflow import FactCheckWorkflow
from app.services.role_gateway_factory import RoleModelGatewayFactory
from app.services.role_runner import GatewayRoleRunner


def build_factcheck_workflow(
    settings: ModelRoutingSettings,
) -> FactCheckWorkflow | None:
    """Не створювати платний workflow без налаштованого ключа."""

    if not settings.enabled:
        return None
    factory = RoleModelGatewayFactory(settings)
    runner = GatewayRoleRunner(factory)
    policy = RoleExecutionPolicy(
        settings.execution_mode,
        max_cost_usd=settings.max_report_cost_usd,
    )
    return FactCheckWorkflow(runner, policy)
