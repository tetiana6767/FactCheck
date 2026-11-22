"""Тести вебпошуку без реального платного запиту."""

import json

import httpx

from app.config.model_settings import ModelRoutingSettings
from app.schemas.check import Claim
from app.services.openrouter_search_gateway import OpenRouterWebSearchGateway


def _settings(**overrides) -> ModelRoutingSettings:
    values = {
        "api_key": "test-key",
        "web_search_max_claims": 1,
        "web_search_max_results": 2,
        "web_search_max_uses": 2,
    }
    values.update(overrides)
    return ModelRoutingSettings(_env_file=None, **values)


def test_search_converts_only_web_citations_to_evidence() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["tools"][0]["type"] == "openrouter:web_search"
        parameters = payload["tools"][0]["parameters"]
        assert parameters["max_uses"] == 2
        assert parameters["max_total_results"] == 4
        assert "спростування" in payload["messages"][1]["content"]
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "Знайдено джерело.",
                            "annotations": [
                                {
                                    "type": "url_citation",
                                    "url_citation": {
                                        "url": "https://example.org/fact",
                                        "title": "Першоджерело",
                                        "content": "  Перевірений уривок.  ",
                                    },
                                },
                                {"type": "other", "url": "https://fake.test"},
                            ],
                        }
                    }
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    gateway = OpenRouterWebSearchGateway(_settings(), client)
    claim = Claim(id="claim-1", text="Перевірювана теза.", start=0, end=19)

    evidence = gateway.search(claim)

    assert len(evidence) == 1
    assert evidence[0].source_type == "web"
    assert evidence[0].url == "https://example.org/fact"
    assert evidence[0].quote == "Перевірений уривок."


def test_search_respects_claim_limit() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={"choices": [{"message": {"annotations": []}}]},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    gateway = OpenRouterWebSearchGateway(_settings(), client)
    claim = Claim(id="claim-1", text="Перевірювана теза.", start=0, end=19)

    gateway.search(claim)
    gateway.search(claim)

    assert calls == 1
