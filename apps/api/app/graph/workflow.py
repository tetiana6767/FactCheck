"""Послідовний LangGraph із умовними економними вузлами."""

from collections.abc import Callable

from langgraph.graph import END, START, StateGraph

from app.graph.execution_policy import RoleExecutionPolicy
from app.graph.roles import AgentRole
from app.graph.runner import RoleExecutionError, RoleRunner
from app.graph.state import FactCheckGraphState

ROLE_ORDER = (
    AgentRole.CLAIM,
    AgentRole.EVIDENCE,
    AgentRole.SOURCE,
    AgentRole.LINGUISTIC,
    AgentRole.SKEPTIC,
    AgentRole.VERIFIER,
    AgentRole.ARBITER,
)


class FactCheckWorkflow:
    """Скомпілювати й виконати керований граф одного звіту."""

    def __init__(
        self,
        runner: RoleRunner,
        policy: RoleExecutionPolicy | None = None,
    ) -> None:
        self._runner = runner
        self._policy = policy or RoleExecutionPolicy()
        self._graph = self._build_graph()

    def invoke(self, state: FactCheckGraphState) -> FactCheckGraphState:
        """Виконати граф і повернути валідований незмінний стан."""

        result = self._graph.invoke(state)
        return FactCheckGraphState.model_validate(result)

    def _build_graph(self):
        builder = StateGraph(FactCheckGraphState)
        for role in ROLE_ORDER:
            builder.add_node(role.value, self._node(role))
        builder.add_edge(START, ROLE_ORDER[0].value)
        for current, following in zip(ROLE_ORDER, ROLE_ORDER[1:]):
            builder.add_edge(current.value, following.value)
        builder.add_edge(ROLE_ORDER[-1].value, END)
        return builder.compile(name="factcheck-economy-workflow")

    def _node(
        self, role: AgentRole
    ) -> Callable[[FactCheckGraphState], dict[str, object]]:
        def execute(state: FactCheckGraphState) -> dict[str, object]:
            if not self._policy.should_run(role, state):
                return {"skipped_roles": (*state.skipped_roles, role)}
            try:
                result = self._runner.run(role, state)
            except RoleExecutionError as error:
                # Помилка ролі фіксується, але не руйнує весь звіт.
                return {
                    "failed_roles": (*state.failed_roles, role),
                    "role_results": (
                        *state.role_results,
                        error.role_result,
                    ),
                }
            return {
                "completed_roles": (*state.completed_roles, role),
                "role_results": (*state.role_results, result.role_result),
                "preliminary_statuses": (
                    *state.preliminary_statuses,
                    *result.preliminary_statuses,
                ),
                "high_risk": state.high_risk or result.high_risk,
            }

        return execute
