"""Порт виконання ролі та результат одного вузла графа."""

from dataclasses import dataclass
from typing import Protocol

from app.graph.roles import AgentRole
from app.graph.state import FactCheckGraphState
from app.schemas.agent import ClaimStatus
from app.schemas.multi_agent import AgentRoleResult


@dataclass(frozen=True)
class RoleRunResult:
    """Мінімальні доменні зміни після одного агента."""

    role_result: AgentRoleResult
    preliminary_statuses: tuple[ClaimStatus, ...] = ()
    high_risk: bool = False


class RoleExecutionError(RuntimeError):
    """Контрольована відмова одного агента без зупинки графа."""

    def __init__(self, role_result: AgentRoleResult) -> None:
        super().__init__(role_result.run.error_code or "role_execution_failed")
        self.role_result = role_result


class RoleRunner(Protocol):
    """Виконати спеціалізованого агента без залежності від LangGraph."""

    def run(
        self, role: AgentRole, state: FactCheckGraphState
    ) -> RoleRunResult:
        """Повернути доменні зміни або підняти контрольовану помилку."""
