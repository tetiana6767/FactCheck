"""Тести вибору адаптера мовної моделі."""

from app.services.model_factory import build_model_gateway
from app.services.model_gateway import DisabledModelGateway
from app.services.openrouter_gateway import OpenRouterGateway
from app.settings import OpenRouterSettings


def test_factory_uses_disabled_gateway_without_configuration() -> None:
    gateway = build_model_gateway(OpenRouterSettings(api_key=None, model=None))

    assert isinstance(gateway, DisabledModelGateway)


def test_factory_uses_openrouter_with_complete_configuration() -> None:
    settings = OpenRouterSettings(api_key="secret", model="test/model")

    gateway = build_model_gateway(settings)

    assert isinstance(gateway, OpenRouterGateway)
