"""HTTP-маршрути першого етапу FactCheck."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.check import CheckRequest, CheckResponse, HealthResponse
from app.services.check_service import CheckService

router = APIRouter(prefix="/api")


def get_check_service() -> CheckService:
    """Створити сервіс детермінованої перевірки."""

    return CheckService()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Повернути стан готовності API."""

    return HealthResponse(status="ok")


@router.post("/check", response_model=CheckResponse)
def check_claim(
    request: CheckRequest,
    service: Annotated[CheckService, Depends(get_check_service)],
) -> CheckResponse:
    """Перевірити контракт запиту та повернути тестовий звіт."""

    return service.analyze(request)
