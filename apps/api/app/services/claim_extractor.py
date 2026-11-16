"""Детерміноване виділення перевірюваних тверджень."""

import re

from app.schemas.check import Claim

_SENTENCE_PATTERN = re.compile(r"[^.!?]+(?:[.!?]+|$)", re.UNICODE)
_SUBJECTIVE_PATTERN = re.compile(
    r"^(?:на мою думку|я вважаю|мабуть|можливо|ймовірно)\b",
    re.IGNORECASE,
)


class ClaimExtractor:
    """Виділити декларативні речення зі збереженням позицій."""

    def extract(self, text: str) -> tuple[Claim, ...]:
        """Повернути стабільно впорядковані твердження."""

        claims: list[Claim] = []
        for match in _SENTENCE_PATTERN.finditer(text):
            fragment = match.group(0)
            stripped = fragment.strip()
            if not self._is_checkable(stripped):
                continue

            leading_spaces = len(fragment) - len(fragment.lstrip())
            start = match.start() + leading_spaces
            claims.append(
                Claim(
                    id=f"claim-{len(claims) + 1}",
                    text=stripped,
                    start=start,
                    end=start + len(stripped),
                )
            )
        return tuple(claims)

    @staticmethod
    def _is_checkable(text: str) -> bool:
        return (
            len(text) >= 8
            and not text.endswith("?")
            and _SUBJECTIVE_PATTERN.match(text) is None
        )
