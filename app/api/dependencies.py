from functools import lru_cache

from app.application.services.dashboard_service import DashboardService
from app.application.services.confronto_service import ConfrontoService
from app.application.services.equipe_service import EquipeService
from app.core.config import get_settings
from app.domain.repositories.confronto_repository import ConfrontoRepository
from app.domain.repositories.equipe_repository import EquipeRepository
from app.infrastructure.persistence.firestore.firestore_client import FirestoreDatabase
from app.infrastructure.repositories.firestore_confronto_repository import FirestoreConfrontoRepository
from app.infrastructure.repositories.firestore_equipe_repository import FirestoreEquipeRepository


@lru_cache
def get_database() -> FirestoreDatabase:
    settings = get_settings()
    return FirestoreDatabase(
        project_id=settings.google_cloud_project,
        equipes_collection=settings.firestore_equipes_collection,
        confrontos_collection=settings.firestore_confrontos_collection,
    )


def get_equipe_repository() -> EquipeRepository:
    return FirestoreEquipeRepository(get_database())


def get_confronto_repository() -> ConfrontoRepository:
    return FirestoreConfrontoRepository(get_database())


def get_equipe_service() -> EquipeService:
    return EquipeService(get_equipe_repository())


def get_confronto_service() -> ConfrontoService:
    return ConfrontoService(get_confronto_repository())


def get_dashboard_service() -> DashboardService:
    return DashboardService(
        equipe_repository=get_equipe_repository(),
        confronto_repository=get_confronto_repository(),
    )
