"""HTTP-маршрути першого етапу FactCheck."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.config.model_settings import ModelRoutingSettings
from app.schemas.check import CheckRequest, CheckResponse, HealthResponse
from app.services.check_service import CheckService
from app.services.workflow_factory import build_factcheck_workflow

router = APIRouter(prefix="/api")


def get_check_service() -> CheckService:
    """Створити сервіс перевірки з адаптером із конфігурації."""

    settings = ModelRoutingSettings()
    return CheckService(
        workflow=build_factcheck_workflow(settings),
        execution_mode=settings.execution_mode,
    )


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
