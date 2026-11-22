"""Композиція пошукових адаптерів із конфігурації."""

from app.config.model_settings import ModelRoutingSettings
from app.services.openrouter_search_gateway import OpenRouterWebSearchGateway
from app.services.search_gateway import (
    CompositeSearchGateway,
    InMemorySearchGateway,
    SearchGateway,
)


def build_search_gateway(settings: ModelRoutingSettings) -> SearchGateway:
    """Додати вебпошук лише за наявності безпечної конфігурації."""

    local = InMemorySearchGateway()
    if not settings.web_search_ready:
        return local
    return CompositeSearchGateway(
        (local, OpenRouterWebSearchGateway(settings))
    )
