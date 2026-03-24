from collections.abc import Callable
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.services.auth_service import AuthService
from app.application.services.dashboard_service import DashboardService
from app.application.services.confronto_service import ConfrontoService
from app.application.services.equipe_service import EquipeService
from app.application.services.usuario_service import UsuarioService
from app.core.config import get_settings
from app.domain.entities.usuario import RoleUsuario, Usuario
from app.domain.repositories.confronto_repository import ConfrontoRepository
from app.domain.repositories.equipe_repository import EquipeRepository
from app.domain.repositories.usuario_repository import UsuarioRepository
from app.infrastructure.persistence.firestore.firestore_client import FirestoreDatabase
from app.infrastructure.repositories.firestore_confronto_repository import FirestoreConfrontoRepository
from app.infrastructure.repositories.firestore_equipe_repository import FirestoreEquipeRepository
from app.infrastructure.repositories.firestore_usuario_repository import FirestoreUsuarioRepository

security_scheme = HTTPBearer(auto_error=False)


@lru_cache
def get_database() -> FirestoreDatabase:
    settings = get_settings()
    return FirestoreDatabase(
        project_id=settings.google_cloud_project,
        equipes_collection=settings.firestore_equipes_collection,
        confrontos_collection=settings.firestore_confrontos_collection,
        usuarios_collection=settings.firestore_usuarios_collection,
    )


def get_equipe_repository() -> EquipeRepository:
    return FirestoreEquipeRepository(get_database())


def get_confronto_repository() -> ConfrontoRepository:
    return FirestoreConfrontoRepository(get_database())


def get_usuario_repository() -> UsuarioRepository:
    return FirestoreUsuarioRepository(get_database())


def get_equipe_service() -> EquipeService:
    return EquipeService(get_equipe_repository())


def get_confronto_service() -> ConfrontoService:
    return ConfrontoService(get_confronto_repository())


def get_usuario_service() -> UsuarioService:
    return UsuarioService(get_usuario_repository())


def get_auth_service() -> AuthService:
    return AuthService(get_usuario_repository(), get_settings())


def get_dashboard_service() -> DashboardService:
    return DashboardService(
        equipe_repository=get_equipe_repository(),
        confronto_repository=get_confronto_repository(),
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> Usuario:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticacao obrigatoria.",
        )

    return auth_service.obter_usuario_atual(credentials.credentials)


def require_roles(*roles: RoleUsuario) -> Callable[[Usuario], Usuario]:
    def dependency(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Voce nao tem permissao para esta acao.",
            )
        return current_user

    return dependency
