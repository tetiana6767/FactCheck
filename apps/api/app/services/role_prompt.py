"""Окремі інструкції для спеціалізованих агентів."""

from app.graph.roles import AgentRole
from app.services.agent_prompt import AgentPromptBuilder
from app.services.model_gateway import ModelContext

ROLE_INSTRUCTIONS = {
    AgentRole.CLAIM: (
        "Перевір повноту й атомарність виділених тез. Не додавай нових фактів."
    ),
    AgentRole.EVIDENCE: (
        "Зістав кожну тезу лише з цитатами у EvidenceSnapshot. "
        "Без прямого доказу обирай insufficient_evidence."
    ),
    AgentRole.SOURCE: (
        "Оціни придатність наданих джерел для конкретних тез. "
        "Не роби висновків про джерела за межами наданих метаданих."
    ),
    AgentRole.LINGUISTIC: (
        "Опиши мовні сигнали маніпулятивності. Вони не доводять неправдивість."
    ),
    AgentRole.SKEPTIC: (
        "Шукай альтернативні пояснення, слабкі місця й пропущені контрдокази."
    ),
    AgentRole.VERIFIER: (
        "Повторно перевір суперечливі оцінки за тим самим знімком доказів."
    ),
    AgentRole.ARBITER: (
        "Узагальни доступні оцінки консервативно. За браку прямих доказів "
        "залишай insufficient_evidence."
    ),
}


class RolePromptBuilder(AgentPromptBuilder):
    """Додати рольову інструкцію до спільного безпечного промпта."""

    def __init__(self, role: AgentRole) -> None:
        self._role = role

    def build_messages(self, context: ModelContext) -> list[dict[str, str]]:
        """Побудувати повідомлення зі стислою спеціалізацією ролі."""

        messages = super().build_messages(context)
        system = messages[0]["content"]
        messages[0]["content"] = (
            f"{system}\nРоль: {self._role.value}. "
            f"{ROLE_INSTRUCTIONS[self._role]}\n"
            "Поле confidence має відображати впевненість лише за наданими "
            "даними. Познач high_risk=true для суттєвої суперечності або "
            "небезпечного висновку з недостатніх даних."
        )
        return messages
