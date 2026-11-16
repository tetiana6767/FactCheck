"""Прозорий baseline мовних сигналів маніпулятивності."""

import re

from app.schemas.agent import LinguisticFlag

SENSATIONAL_PATTERNS = (
    "ви не повірите",
    "неймовірно",
    "сенсація",
    "терміново",
    "шок",
)
UPPERCASE_TOKEN = re.compile(r"\b[А-ЯІЇЄҐA-Z]{3,}\b")
PUNCTUATION_CLUSTER = re.compile(r"[!?]{3,}")


class LinguisticAnalyzer:
    """Знайти пояснювані сигнали без фактичного вердикту."""

    def analyze(self, text: str) -> tuple[LinguisticFlag, ...]:
        """Повернути детерміновані мовні спостереження."""

        flags: list[LinguisticFlag] = []
        lowered = text.casefold()
        for pattern in SENSATIONAL_PATTERNS:
            if pattern in lowered:
                flags.append(
                    LinguisticFlag(
                        kind="sensational_phrase",
                        fragment=pattern,
                        explanation="Виявлено сенсаційну або термінову лексику.",
                    )
                )

        uppercase = UPPERCASE_TOKEN.search(text)
        if uppercase is not None:
            flags.append(
                LinguisticFlag(
                    kind="uppercase_emphasis",
                    fragment=uppercase.group(),
                    explanation="Великі літери можуть підсилювати емоційний тон.",
                )
            )

        punctuation = PUNCTUATION_CLUSTER.search(text)
        if punctuation is not None:
            flags.append(
                LinguisticFlag(
                    kind="excessive_punctuation",
                    fragment=punctuation.group(),
                    explanation="Повторювані знаки можуть створювати емоційний тиск.",
                )
            )
        return tuple(flags)
