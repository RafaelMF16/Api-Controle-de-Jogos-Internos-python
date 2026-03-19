from fastapi import APIRouter, Depends

from app.api.dependencies import get_dashboard_service
from app.application.dtos.dashboard_dto import ResumoDashboard
from app.application.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# Retorna os totais e a lista resumida de proximos confrontos exibidos no dashboard do front-end.
@router.get("/resumo", response_model=ResumoDashboard, summary="Obter resumo do dashboard")
def get_overview(service: DashboardService = Depends(get_dashboard_service)) -> ResumoDashboard:
    return service.get_overview()
