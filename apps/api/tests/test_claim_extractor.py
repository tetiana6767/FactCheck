"""Тести виділення перевірюваних тверджень."""

from app.services.claim_extractor import ClaimExtractor


def test_extractor_preserves_text_offsets() -> None:
    text = "  Київ — столиця України. Вода замерзає при 0 °C."

    claims = ClaimExtractor().extract(text)

    assert [claim.id for claim in claims] == ["claim-1", "claim-2"]
    assert [text[claim.start : claim.end] for claim in claims] == [
        claim.text for claim in claims
    ]


def test_extractor_skips_questions_and_subjective_phrases() -> None:
    text = "Можливо, це станеться завтра. Коли це станеться? Земля обертається."

    claims = ClaimExtractor().extract(text)

    assert [claim.text for claim in claims] == ["Земля обертається."]
