"""Детермінований сервіс перевірки для наскрізного каркаса."""

from app.schemas.check import CheckRequest, CheckResponse


class CheckService:
    """Сформувати прозорий результат без зовнішніх джерел."""

    def analyze(self, request: CheckRequest) -> CheckResponse:
        """Повернути нейтральний звіт до підключення доказів."""

        return CheckResponse(
            claim=request.claim,
            verdict="insufficient_evidence",
            explanation=(
                "Твердження прийнято до аналізу. Пошук і перевірку джерел "
                "буде підключено на наступному етапі, тому доказів для "
                "фактологічного висновку поки недостатньо."
            ),
        )
