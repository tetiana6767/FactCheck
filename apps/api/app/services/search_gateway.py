"""Пошуковий порт і локальний адаптер контрольованого корпусу."""

import re
from dataclasses import dataclass
from typing import Mapping, Protocol

from app.schemas.check import Claim, Evidence


class SearchGateway(Protocol):
    """Знайти докази для одного перевірюваного твердження."""

    def search(self, claim: Claim) -> tuple[Evidence, ...]:
        """Повернути впорядковані записи доказів."""


@dataclass(frozen=True)
class EvidenceRecord:
    """Запис локального тестового корпусу без прив'язки до запиту."""

    id: str
    title: str
    url: str
    quote: str
    source_date: str | None = None


DEFAULT_TEST_CORPUS: Mapping[str, tuple[EvidenceRecord, ...]] = {
    "київ столиця україни": (
        EvidenceRecord(
            id="test-kyiv-capital-1",
            title="Навчальний запис про столицю України",
            url="urn:factcheck:test-corpus:kyiv-capital",
            quote="Київ є столицею України.",
            source_date="2026-11-16",
        ),
    ),
    "вода замерзає при 0 °c": (
        EvidenceRecord(
            id="test-water-freezing-1",
            title="Навчальний запис про температуру замерзання води",
            url="urn:factcheck:test-corpus:water-freezing",
            quote="За стандартного атмосферного тиску чиста вода замерзає при 0 °C.",
            source_date="2026-11-16",
        ),
    ),
}


class InMemorySearchGateway:
    """Шукати точні нормалізовані збіги у тестовому корпусі."""

    def __init__(
        self,
        corpus: Mapping[str, tuple[EvidenceRecord, ...]] = DEFAULT_TEST_CORPUS,
    ) -> None:
        self._corpus = {
            self._normalize(key): records for key, records in corpus.items()
        }

    def search(self, claim: Claim) -> tuple[Evidence, ...]:
        """Прив'язати знайдені записи до ID твердження."""

        records = self._corpus.get(self._normalize(claim.text), ())
        return tuple(
            Evidence(
                id=record.id,
                claim_id=claim.id,
                title=record.title,
                url=record.url,
                quote=record.quote,
                source_date=record.source_date,
                source_type="test_corpus",
            )
            for record in records
        )

    @staticmethod
    def _normalize(text: str) -> str:
        lowered = text.casefold().replace("—", " ").replace("–", " ")
        without_punctuation = re.sub(r"[^\w°]+", " ", lowered, flags=re.UNICODE)
        return " ".join(without_punctuation.split())
