"""Baseline-класифікатор тексту у стилі scikit-learn."""

from collections.abc import Sequence
from typing import Any, Self

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.utils.validation import check_is_fitted


class TextCredibilityBaseline(ClassifierMixin, BaseEstimator):
    """TF-IDF та Logistic Regression для контрольного порівняння."""

    def __init__(
        self,
        *,
        max_features: int = 20_000,
        regularization: float = 1.0,
        random_state: int = 42,
    ) -> None:
        self.max_features = max_features
        self.regularization = regularization
        self.random_state = random_state

    def fit(self, X: Sequence[str], y: Sequence[str]) -> Self:
        """Навчити відтворюваний pipeline на розмічених текстах."""

        texts = self._validate_texts(X)
        self.pipeline_ = Pipeline(
            steps=[
                (
                    "tfidf",
                    TfidfVectorizer(
                        analyzer="char_wb",
                        ngram_range=(3, 5),
                        lowercase=True,
                        max_features=self.max_features,
                    ),
                ),
                (
                    "classifier",
                    LogisticRegression(
                        C=self.regularization,
                        class_weight="balanced",
                        max_iter=1_000,
                        random_state=self.random_state,
                    ),
                ),
            ]
        )
        self.pipeline_.fit(texts, y)
        self.classes_ = self.pipeline_.classes_
        return self

    def predict(self, X: Sequence[str]) -> np.ndarray:
        """Передбачити клас для кожного тексту."""

        check_is_fitted(self, "pipeline_")
        return self.pipeline_.predict(self._validate_texts(X))

    def predict_proba(self, X: Sequence[str]) -> np.ndarray:
        """Повернути ймовірності класів для експерименту."""

        check_is_fitted(self, "pipeline_")
        return self.pipeline_.predict_proba(self._validate_texts(X))

    @staticmethod
    def _validate_texts(values: Sequence[str]) -> list[str]:
        texts = list(values)
        if not texts:
            raise ValueError("At least one text is required")
        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ValueError("Every text must be a non-empty string")
        return texts

    def _more_tags(self) -> dict[str, Any]:
        return {"X_types": ["string"]}
