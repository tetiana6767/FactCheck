"""Ізольовані тести HTTP-адаптера OpenRouter."""

import json

import httpx

from app.schemas.check import Claim, EvidenceSnapshot
from app.services.agent_prompt import AgentPromptBuilder
from app.services.model_gateway import ModelContext
from app.services.openrouter_gateway import OpenRouterGateway
from app.settings import OpenRouterSettings

ENDPOINT = "https://openrouter.test/api/v1/chat/completions"


def _context() -> ModelContext:
    return ModelContext(
        text="Київ — столиця України.",
        claims=(
            Claim(
                id="claim-1",
                text="Київ — столиця України.",
                start=0,
                end=23,
            ),
        ),
        evidence_snapshot=EvidenceSnapshot(),
    )


def _settings() -> OpenRouterSettings:
    return OpenRouterSettings(
        api_key="test-secret",
        model="test/model",
        endpoint=ENDPOINT,
        retry_delay_seconds=0,
    )


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_response_schema_requires_every_declared_property() -> None:
    response_format = AgentPromptBuilder().build_response_format()
    schema = response_format["json_schema"]["schema"]

    assert set(schema["required"]) == set(schema["properties"])
    for definition in schema["$defs"].values():
        assert definition["additionalProperties"] is False
        assert set(definition["required"]) == set(definition["properties"])


def test_gateway_returns_validated_analysis_and_usage() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert request.headers["Authorization"] == "Bearer test-secret"
        assert payload["provider"] == {"require_parameters": True}
        assert payload["response_format"]["json_schema"]["strict"] is True
        content = {
            "summary": "Доказів недостатньо.",
            "linguistic_flags": [],
            "claim_assessments": [
                {
                    "claim_id": "claim-1",
                    "status": "insufficient_evidence",
                    "rationale": "Знімок доказів порожній.",
                    "evidence_ids": [],
                }
            ],
            "uncertainties": ["Зовнішні джерела не перевірено."],
        }
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": json.dumps(content)}}],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 40,
                    "total_tokens": 140,
                },
            },
        )

    with _client(handler) as client:
        result = OpenRouterGateway(_settings(), client=client).analyze(_context())

    assert result.run.status == "completed"
    assert result.run.total_tokens == 140
    assert result.analysis is not None
    assert result.analysis.claim_assessments[0].claim_id == "claim-1"


def test_gateway_rejects_invalid_structured_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"summary": 1}'}}]},
        )

    with _client(handler) as client:
        result = OpenRouterGateway(_settings(), client=client).analyze(_context())

    assert result.analysis is None
    assert result.run.status == "invalid_response"
    assert result.run.error_code == "openrouter_invalid_response"


def test_gateway_maps_provider_error_without_leaking_body() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(429, json={"error": "sensitive"}, request=request)

    with _client(handler) as client:
        result = OpenRouterGateway(_settings(), client=client).analyze(_context())

    assert result.analysis is None
    assert result.run.status == "provider_error"
    assert result.run.error_code == "openrouter_http_429"
    assert attempts == 3


def test_gateway_recovers_after_temporary_provider_error() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, request=request)
        content = {
            "summary": "Аналіз завершено.",
            "linguistic_flags": [],
            "claim_assessments": [],
            "uncertainties": [],
        }
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(content)}}]},
        )

    with _client(handler) as client:
        result = OpenRouterGateway(_settings(), client=client).analyze(_context())

    assert result.run.status == "completed"
    assert attempts == 2


def test_gateway_maps_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout", request=request)

    with _client(handler) as client:
        result = OpenRouterGateway(_settings(), client=client).analyze(_context())

    assert result.analysis is None
    assert result.run.status == "timeout"
    assert result.run.error_code == "openrouter_timeout"
