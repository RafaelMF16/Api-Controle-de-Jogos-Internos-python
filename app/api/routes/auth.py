from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_auth_service, get_current_user, get_usuario_service
from app.application.dtos.auth_dto import AuthResponse, LoginInput, VisitorSignupInput
from app.application.dtos.usuario_dto import UsuarioOutput
from app.application.services.auth_service import AuthService
from app.application.services.usuario_service import UsuarioService
from app.domain.entities.usuario import Usuario

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=AuthResponse, summary="Realizar login")
def login(payload: LoginInput, service: AuthService = Depends(get_auth_service)) -> AuthResponse:
    token, usuario = service.autenticar(payload.username, payload.senha)
    return AuthResponse(
        accessToken=token,
        user=UsuarioOutput.from_entity(usuario),
    )


@router.post("/register-visitor", response_model=AuthResponse, status_code=status.HTTP_201_CREATED, summary="Cadastrar visitante")
def register_visitor(
    payload: VisitorSignupInput,
    usuario_service: UsuarioService = Depends(get_usuario_service),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    usuario = usuario_service.registrar_visitante(payload)
    token, usuario_autenticado = auth_service.autenticar(usuario.username, payload.senha)
    return AuthResponse(
        accessToken=token,
        user=UsuarioOutput.from_entity(usuario_autenticado),
    )


@router.get("/me", response_model=UsuarioOutput, summary="Obter usuário autenticado")
def me(current_user: Usuario = Depends(get_current_user)) -> UsuarioOutput:
    return UsuarioOutput.from_entity(current_user)
