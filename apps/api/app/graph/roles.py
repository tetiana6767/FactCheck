"""Стабільні ідентифікатори спеціалізованих агентів."""

from enum import StrEnum


class AgentRole(StrEnum):
    """Ролі мультиагентного аналізу."""

    CLAIM = "claim"
    EVIDENCE = "evidence"
    SOURCE = "source"
    LINGUISTIC = "linguistic"
    SKEPTIC = "skeptic"
    VERIFIER = "verifier"
    ARBITER = "arbiter"
