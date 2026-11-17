"""Тести економної рольової маршрутизації моделей."""

import os

import pytest
from pydantic import ValidationError

from app.config.model_registry import ModelRegistry
from app.config.model_settings import ModelRoutingSettings
from app.graph.roles import AgentRole
from app.services.model_gateway import DisabledModelGateway
from app.services.openrouter_gateway import OpenRouterGateway
from app.services.role_gateway_factory import RoleModelGatewayFactory


@pytest.fixture(autouse=True)
def clear_openrouter_environment(monkeypatch) -> None:
    """Не дозволити локальним секретам вплинути на unit-тести."""

    for name in tuple(os.environ):
        if name.startswith("OPENROUTER_"):
            monkeypatch.delenv(name, raising=False)


def test_default_role_models_fit_gpt_4o_mini_price_ceiling() -> None:
    registry = ModelRegistry(ModelRoutingSettings(_env_file=None))

    assert registry.default_models_fit_price_ceiling() is True
    assert registry.profile(AgentRole.EVIDENCE).model_id.startswith("deepseek/")
    assert registry.profile(AgentRole.SOURCE).model_id.startswith("qwen/")
    assert registry.profile(AgentRole.ARBITER).model_id == "openai/gpt-4o-mini"


def test_single_mode_routes_every_role_to_default_model() -> None:
    settings = ModelRoutingSettings(
        _env_file=None,
        routing_mode="single",
        model_default="openai/gpt-4o-mini",
    )
    registry = ModelRegistry(settings)

    assert {profile.model_id for profile in registry.all_profiles()} == {
        "openai/gpt-4o-mini"
    }


def test_role_limits_reduce_output_tokens() -> None:
    settings = ModelRoutingSettings(_env_file=None, max_tokens=1_200)
    registry = ModelRegistry(settings)

    assert registry.profile(AgentRole.LINGUISTIC).max_tokens == 400
    assert registry.profile(AgentRole.EVIDENCE).max_tokens == 1_000


def test_factory_disables_network_without_key() -> None:
    settings = ModelRoutingSettings(_env_file=None, api_key=None)

    gateway = RoleModelGatewayFactory(settings).build(AgentRole.ARBITER)

    assert isinstance(gateway, DisabledModelGateway)


def test_factory_uses_role_model_with_key() -> None:
    settings = ModelRoutingSettings(_env_file=None, api_key="secret")
    factory = RoleModelGatewayFactory(settings)

    gateway = factory.build(AgentRole.EVIDENCE)
    runtime = factory.runtime_settings(AgentRole.EVIDENCE)

    assert isinstance(gateway, OpenRouterGateway)
    assert runtime.model == "deepseek/deepseek-v4.1-flash-20260910"
    assert runtime.max_tokens == 1_000
    assert runtime.fallback_models == (
        "mistralai/mistral-small-3.2-24b-instruct",
    )
    assert runtime.max_input_price_per_million == 0.15
    assert runtime.max_output_price_per_million == 0.60


def test_settings_reject_invalid_mode_and_model_id() -> None:
    with pytest.raises(ValidationError):
        ModelRoutingSettings(_env_file=None, routing_mode="random")
    with pytest.raises(ValidationError):
        ModelRoutingSettings(_env_file=None, model_claim="invalid")
