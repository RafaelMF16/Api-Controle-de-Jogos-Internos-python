from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import get_auth_service, get_current_user, get_usuario_service
from app.application.dtos.auth_dto import AuthResponse, LoginInput, VisitorSignupInput
from app.application.dtos.usuario_dto import UsuarioOutput, UsuarioTemaInput
from app.application.services.auth_service import AuthService
from app.application.services.usuario_service import UsuarioService
from app.core.config import get_settings
from app.domain.entities.usuario import Usuario

router = APIRouter(prefix="/auth", tags=["Autenticacao"])
settings = get_settings()


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.auth_cookie_name,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path="/",
    )


@router.post("/login", response_model=AuthResponse, summary="Realizar login")
def login(
    payload: LoginInput,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    token, usuario = service.autenticar(payload.username, payload.senha)
    _set_auth_cookie(response, token)
    return AuthResponse(
        user=UsuarioOutput.from_entity(usuario),
    )


@router.post("/register-visitor", response_model=AuthResponse, status_code=status.HTTP_201_CREATED, summary="Cadastrar visitante")
def register_visitor(
    payload: VisitorSignupInput,
    response: Response,
    usuario_service: UsuarioService = Depends(get_usuario_service),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    usuario = usuario_service.registrar_visitante(payload)
    token, usuario_autenticado = auth_service.autenticar(usuario.username, payload.senha)
    _set_auth_cookie(response, token)
    return AuthResponse(
        user=UsuarioOutput.from_entity(usuario_autenticado),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Encerrar sessao")
def logout(response: Response) -> Response:
    _clear_auth_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UsuarioOutput, summary="Obter usuario autenticado")
def me(current_user: Usuario = Depends(get_current_user)) -> UsuarioOutput:
    return UsuarioOutput.from_entity(current_user)


@router.put("/me/tema", response_model=UsuarioOutput, summary="Atualizar tema do usuario autenticado")
def atualizar_tema(
    payload: UsuarioTemaInput,
    current_user: Usuario = Depends(get_current_user),
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioOutput:
    usuario = service.atualizar_tema(current_user.id, payload.tema)
    if usuario is None:
        return UsuarioOutput.from_entity(current_user)
    return UsuarioOutput.from_entity(usuario)
