"""HTTP-адаптер структурованих відповідей OpenRouter."""

import json
from time import perf_counter, sleep
from typing import Any

import httpx
from pydantic import ValidationError

from app.schemas.agent import (
    ModelResult,
    ModelRun,
    ModelStatus,
    SingleAgentAnalysis,
)
from app.services.agent_prompt import AgentPromptBuilder
from app.services.model_gateway import ModelContext
from app.settings import OpenRouterSettings


class OpenRouterGateway:
    """Виконати один контрольований запит до OpenRouter."""

    def __init__(
        self,
        settings: OpenRouterSettings,
        client: httpx.Client | None = None,
        prompt_builder: AgentPromptBuilder | None = None,
    ) -> None:
        if not settings.enabled:
            raise ValueError("OpenRouter settings are incomplete")
        self._settings = settings
        self._client = client
        self._prompt_builder = prompt_builder or AgentPromptBuilder()

    def analyze(self, context: ModelContext) -> ModelResult:
        """Надіслати запит і перетворити відповідь на безпечний результат."""

        started_at = perf_counter()
        try:
            response = self._post_with_retries(self._build_payload(context))
            response.raise_for_status()
            return self._parse_response(response, started_at)
        except httpx.TimeoutException:
            return self._failure("timeout", "openrouter_timeout", started_at)
        except httpx.HTTPStatusError as error:
            code = f"openrouter_http_{error.response.status_code}"
            return self._failure("provider_error", code, started_at)
        except httpx.RequestError:
            return self._failure(
                "provider_error", "openrouter_transport_error", started_at
            )

    def _build_payload(self, context: ModelContext) -> dict[str, Any]:
        return {
            "model": self._settings.model,
            "messages": self._prompt_builder.build_messages(context),
            "response_format": self._prompt_builder.build_response_format(),
            "provider": {"require_parameters": True},
            "temperature": 0,
            "max_tokens": self._settings.max_tokens,
        }

    def _post(self, payload: dict[str, Any]) -> httpx.Response:
        headers = {
            "Authorization": f"Bearer {self._settings.api_key}",
            "Content-Type": "application/json",
        }
        if self._client is not None:
            return self._client.post(
                self._settings.endpoint,
                headers=headers,
                json=payload,
                timeout=self._settings.timeout_seconds,
            )
        with httpx.Client(timeout=self._settings.timeout_seconds) as client:
            return client.post(self._settings.endpoint, headers=headers, json=payload)

    def _post_with_retries(self, payload: dict[str, Any]) -> httpx.Response:
        """Повторити лише тимчасові відповіді провайдера."""

        for attempt in range(self._settings.max_retries + 1):
            response = self._post(payload)
            if not self._is_retryable(response) or attempt == self._settings.max_retries:
                return response
            sleep(self._settings.retry_delay_seconds)
        raise RuntimeError("Unreachable retry state")

    @staticmethod
    def _is_retryable(response: httpx.Response) -> bool:
        return response.status_code == 429 or response.status_code >= 500

    def _parse_response(
        self, response: httpx.Response, started_at: float
    ) -> ModelResult:
        try:
            envelope = response.json()
            content = envelope["choices"][0]["message"]["content"]
            analysis = SingleAgentAnalysis.model_validate(json.loads(content))
            usage = envelope.get("usage", {})
        except (json.JSONDecodeError, KeyError, IndexError, TypeError, ValidationError):
            return self._failure(
                "invalid_response", "openrouter_invalid_response", started_at
            )

        return ModelResult(
            analysis=analysis,
            run=ModelRun(
                mode="openrouter",
                model=self._settings.model,
                status="completed",
                latency_ms=self._elapsed_ms(started_at),
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
            ),
        )

    def _failure(
        self, status: ModelStatus, error_code: str, started_at: float
    ) -> ModelResult:
        return ModelResult(
            run=ModelRun(
                mode="openrouter",
                model=self._settings.model,
                status=status,
                latency_ms=self._elapsed_ms(started_at),
                error_code=error_code,
            )
        )

    @staticmethod
    def _elapsed_ms(started_at: float) -> int:
        return max(0, round((perf_counter() - started_at) * 1_000))
