"""Тести прозорого мовного baseline."""

from app.services.linguistic_analyzer import LinguisticAnalyzer


def test_analyzer_finds_explainable_signals() -> None:
    flags = LinguisticAnalyzer().analyze("ТЕРМІНОВО!!! Ви не повірите цій новині")

    kinds = {flag.kind for flag in flags}
    assert kinds == {
        "sensational_phrase",
        "uppercase_emphasis",
        "excessive_punctuation",
    }


def test_analyzer_does_not_label_neutral_text() -> None:
    flags = LinguisticAnalyzer().analyze("Київ — столиця України.")

    assert flags == ()
