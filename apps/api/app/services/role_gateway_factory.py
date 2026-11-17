"""Фабрика модельних gateway для спеціалізованих ролей."""

from app.config.model_registry import ModelRegistry
from app.config.model_settings import ModelRoutingSettings
from app.graph.roles import AgentRole
from app.services.model_gateway import DisabledModelGateway, ModelGateway
from app.services.openrouter_gateway import OpenRouterGateway
from app.services.role_prompt import RolePromptBuilder
from app.settings import OpenRouterSettings


class RoleModelGatewayFactory:
    """Ізолювати створення рольового адаптера від доменного графа."""

    def __init__(
        self,
        settings: ModelRoutingSettings,
        registry: ModelRegistry | None = None,
    ) -> None:
        self._settings = settings
        self._registry = registry or ModelRegistry(settings)

    def build(self, role: AgentRole) -> ModelGateway:
        """Створити OpenRouter gateway або безпечний вимкнений адаптер."""

        if not self._settings.enabled:
            return DisabledModelGateway()
        return OpenRouterGateway(
            self.runtime_settings(role),
            prompt_builder=RolePromptBuilder(role),
        )

    def runtime_settings(self, role: AgentRole) -> OpenRouterSettings:
        """Перетворити профіль ролі на налаштування HTTP-адаптера."""

        profile = self._registry.profile(role)
        api_key = ""
        if self._settings.api_key is not None:
            api_key = self._settings.api_key.get_secret_value().strip()
        return OpenRouterSettings(
            api_key=api_key or None,
            model=profile.model_id,
            endpoint=self._settings.endpoint,
            timeout_seconds=self._settings.timeout_seconds,
            max_tokens=profile.max_tokens,
            max_retries=self._settings.max_retries,
            fallback_models=(
                (profile.fallback_model,)
                if profile.fallback_model is not None
                else ()
            ),
            max_input_price_per_million=(
                self._settings.max_input_price_per_million
            ),
            max_output_price_per_million=(
                self._settings.max_output_price_per_million
            ),
        )
