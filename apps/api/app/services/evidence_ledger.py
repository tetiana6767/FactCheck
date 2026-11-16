"""Реєстр і незмінний знімок доказів."""

from app.schemas.check import Evidence, EvidenceSnapshot


class EvidenceLedger:
    """Зібрати унікальні докази зі стабільним порядком."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, str], Evidence] = {}

    def add(self, evidence: Evidence) -> None:
        """Додати доказ, якщо зв'язок ще не зареєстровано."""

        key = (evidence.claim_id, evidence.id)
        self._items.setdefault(key, evidence)

    def extend(self, evidence_items: tuple[Evidence, ...]) -> None:
        """Додати впорядковану послідовність доказів."""

        for evidence in evidence_items:
            self.add(evidence)

    def snapshot(self) -> EvidenceSnapshot:
        """Повернути незмінний знімок поточного реєстру."""

        return EvidenceSnapshot(items=tuple(self._items.values()))
