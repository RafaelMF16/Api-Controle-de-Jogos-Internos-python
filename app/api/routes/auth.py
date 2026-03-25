from fastapi import APIRouter, Depends

from app.api.dependencies import get_auth_service, get_current_user
from app.application.dtos.auth_dto import AuthResponse, LoginInput
from app.application.dtos.usuario_dto import UsuarioOutput
from app.application.services.auth_service import AuthService
from app.domain.entities.usuario import Usuario

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=AuthResponse, summary="Realizar login")
def login(payload: LoginInput, service: AuthService = Depends(get_auth_service)) -> AuthResponse:
    token, usuario = service.autenticar(payload.email, payload.senha)
    return AuthResponse(
        accessToken=token,
        user=UsuarioOutput.from_entity(usuario),
    )


@router.get("/me", response_model=UsuarioOutput, summary="Obter usuário autenticado")
def me(current_user: Usuario = Depends(get_current_user)) -> UsuarioOutput:
    return UsuarioOutput.from_entity(current_user)
