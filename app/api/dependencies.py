from functools import lru_cache

from app.application.services.dashboard_service import DashboardService
from app.application.services.confronto_service import ConfrontoService
from app.application.services.equipe_service import EquipeService
from app.core.config import get_settings
from app.domain.repositories.confronto_repository import ConfrontoRepository
from app.domain.repositories.equipe_repository import EquipeRepository
from app.infrastructure.persistence.json_db.json_database import JsonDatabase
from app.infrastructure.repositories.json_confronto_repository import JsonConfrontoRepository
from app.infrastructure.repositories.json_equipe_repository import JsonEquipeRepository


@lru_cache
def get_database() -> JsonDatabase:
    settings = get_settings()
    return JsonDatabase(settings.database_file)


def get_equipe_repository() -> EquipeRepository:
    return JsonEquipeRepository(get_database())


def get_confronto_repository() -> ConfrontoRepository:
    return JsonConfrontoRepository(get_database())


def get_equipe_service() -> EquipeService:
    return EquipeService(get_equipe_repository())


def get_confronto_service() -> ConfrontoService:
    return ConfrontoService(get_confronto_repository())


def get_dashboard_service() -> DashboardService:
    return DashboardService(
        equipe_repository=get_equipe_repository(),
        confronto_repository=get_confronto_repository(),
    )
