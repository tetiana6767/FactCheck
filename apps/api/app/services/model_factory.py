"""Композиція адаптера мовної моделі з конфігурації."""

from app.services.model_gateway import DisabledModelGateway, ModelGateway
from app.services.openrouter_gateway import OpenRouterGateway
from app.settings import OpenRouterSettings


def build_model_gateway(
    settings: OpenRouterSettings | None = None,
) -> ModelGateway:
    """Вибрати OpenRouter або безпечний вимкнений режим."""

    resolved = settings or OpenRouterSettings.from_env()
    if not resolved.enabled:
        return DisabledModelGateway()
    return OpenRouterGateway(resolved)
