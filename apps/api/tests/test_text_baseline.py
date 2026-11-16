"""Тести scikit-learn baseline-класифікатора."""

import numpy as np
import pytest
from sklearn.exceptions import NotFittedError

from app.ml.text_baseline import TextCredibilityBaseline

TEXTS = [
    "Офіційний звіт містить методику та посилання на дані.",
    "Дослідження опубліковано з описом вибірки.",
    "ВИ НЕ ПОВІРИТЕ!!! Прихована правда без жодних доказів.",
    "ШОК! Усі ЗМІ мовчать про сенсацію.",
]
LABELS = ["reliable", "reliable", "unreliable", "unreliable"]


def test_baseline_follows_fit_predict_contract() -> None:
    estimator = TextCredibilityBaseline(max_features=1_000)

    fitted = estimator.fit(TEXTS, LABELS)
    predictions = estimator.predict(TEXTS)
    probabilities = estimator.predict_proba(TEXTS[:2])

    assert fitted is estimator
    assert predictions.shape == (4,)
    assert probabilities.shape == (2, 2)
    np.testing.assert_allclose(probabilities.sum(axis=1), 1.0)
    assert set(estimator.classes_) == {"reliable", "unreliable"}


def test_baseline_requires_fit_before_prediction() -> None:
    with pytest.raises(NotFittedError):
        TextCredibilityBaseline().predict(["Текст"])


def test_baseline_rejects_empty_text() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        TextCredibilityBaseline().fit([""], ["reliable"])
