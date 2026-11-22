"""Пошук вебджерел через серверний інструмент OpenRouter."""

from __future__ import annotations

import hashlib
from typing import Any

import httpx

from app.config.model_settings import ModelRoutingSettings
from app.schemas.check import Claim, Evidence


class OpenRouterWebSearchGateway:
    """Перетворити підтверджені вебцитати OpenRouter на докази."""

    def __init__(
        self,
        settings: ModelRoutingSettings,
        client: httpx.Client | None = None,
    ) -> None:
        if not settings.web_search_ready:
            raise ValueError("OpenRouter web search is not configured")
        self._settings = settings
        self._client = client
        self._remaining_searches = settings.web_search_max_claims

    def search(self, claim: Claim) -> tuple[Evidence, ...]:
        """Знайти джерела для однієї тези без вигадування URL."""

        if self._remaining_searches <= 0:
            return ()
        self._remaining_searches -= 1
        try:
            response = self._post(self._build_payload(claim))
            response.raise_for_status()
            return self._parse_response(response.json(), claim)
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            return ()

    def _build_payload(self, claim: Claim) -> dict[str, Any]:
        return {
            "model": self._settings.web_search_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Ти шукаєш докази для фактчекінгу, а не намагаєшся "
                        "підтвердити новину. Обов'язково виконай вебпошук. "
                        "Шукай як підтвердження, так і прямі спростування. "
                        "Якщо теза схожа на фейк, знайди офіційні контрдокази "
                        "або матеріали надійних фактчекерів. Не вигадуй посилань "
                        "і не роби висновку без джерел. Відповідай українською."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Перевір твердження у двох напрямках. Спочатку знайди "
                        "незалежні підтвердження, потім окремо пошукай "
                        "спростування за словами «фактчек», «фейк», «неправда» "
                        "або їхніми відповідниками мовою джерела. Надай "
                        f"цитовані результати для твердження: {claim.text}"
                    ),
                },
            ],
            "tools": [
                {
                    "type": "openrouter:web_search",
                    "parameters": {
                        "engine": self._settings.web_search_engine,
                        "mode": self._settings.web_search_mode,
                        "max_results": self._settings.web_search_max_results,
                        "max_total_results": (
                            self._settings.web_search_max_results
                            * self._settings.web_search_max_uses
                        ),
                        "max_uses": self._settings.web_search_max_uses,
                        "max_characters": 1_500,
                    },
                }
            ],
            "tool_choice": "required",
            "max_completion_tokens": 350,
            "temperature": 0,
            "provider": {
                "max_price": {
                    "prompt": self._settings.max_input_price_per_million,
                    "completion": self._settings.max_output_price_per_million,
                }
            },
        }

    def _post(self, payload: dict[str, Any]) -> httpx.Response:
        headers = {
            "Authorization": (
                f"Bearer {self._settings.api_key.get_secret_value()}"
            ),
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

    def _parse_response(
        self, envelope: dict[str, Any], claim: Claim
    ) -> tuple[Evidence, ...]:
        message = envelope["choices"][0]["message"]
        annotations = message.get("annotations", ())
        evidence: list[Evidence] = []
        seen_urls: set[str] = set()

        for annotation in annotations:
            citation = annotation.get("url_citation", annotation)
            url = citation.get("url")
            if annotation.get("type") != "url_citation" or not self._is_url(url):
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)
            content = citation.get("content") or citation.get("snippet")
            evidence.append(
                Evidence(
                    id=self._evidence_id(claim.id, url),
                    claim_id=claim.id,
                    title=citation.get("title") or "Вебджерело",
                    url=url,
                    quote=self._clean_excerpt(content),
                    source_type="web",
                )
            )
        return tuple(evidence)

    @staticmethod
    def _is_url(value: Any) -> bool:
        return isinstance(value, str) and value.startswith(("https://", "http://"))

    @staticmethod
    def _clean_excerpt(value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        cleaned = " ".join(value.split())
        return cleaned[:600] or None

    @staticmethod
    def _evidence_id(claim_id: str, url: str) -> str:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
        return f"web-{claim_id}-{digest}"
