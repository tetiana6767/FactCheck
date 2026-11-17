"""Композиція адаптера мовної моделі з конфігурації."""

from app.config.model_settings import ModelRoutingSettings
from app.graph.roles import AgentRole
from app.services.model_gateway import DisabledModelGateway, ModelGateway
from app.services.openrouter_gateway import OpenRouterGateway
from app.services.role_gateway_factory import RoleModelGatewayFactory
from app.settings import OpenRouterSettings


def build_model_gateway(
    settings: OpenRouterSettings | None = None,
) -> ModelGateway:
    """Вибрати OpenRouter або безпечний вимкнений режим."""

    if settings is None:
        return RoleModelGatewayFactory(ModelRoutingSettings()).build(
            AgentRole.ARBITER
        )
    resolved = settings
    if not resolved.enabled:
        return DisabledModelGateway()
    return OpenRouterGateway(resolved)
