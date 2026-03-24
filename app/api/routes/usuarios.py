from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_usuario_service, require_roles
from app.application.dtos.usuario_dto import UsuarioCreateInput, UsuarioOutput, UsuarioUpdateInput
from app.application.services.usuario_service import UsuarioService
from app.domain.entities.usuario import RoleUsuario, Usuario

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("", response_model=list[UsuarioOutput], summary="Listar usuarios")
def listar_usuarios(
    _: Usuario = Depends(require_roles(RoleUsuario.ADMIN)),
    service: UsuarioService = Depends(get_usuario_service),
) -> list[UsuarioOutput]:
    return [UsuarioOutput.from_entity(usuario) for usuario in service.listar_usuarios()]


@router.post("", response_model=UsuarioOutput, status_code=status.HTTP_201_CREATED, summary="Criar usuario")
def criar_usuario(
    payload: UsuarioCreateInput,
    _: Usuario = Depends(require_roles(RoleUsuario.ADMIN)),
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioOutput:
    usuario = service.criar_usuario(payload)
    return UsuarioOutput.from_entity(usuario)


@router.put("/{usuario_id}", response_model=UsuarioOutput, summary="Atualizar usuario")
def atualizar_usuario(
    usuario_id: int,
    payload: UsuarioUpdateInput,
    current_user: Usuario = Depends(require_roles(RoleUsuario.ADMIN)),
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioOutput:
    if current_user.id == usuario_id and payload.role != RoleUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O administrador logado nao pode remover o proprio acesso de admin.",
        )

    usuario = service.atualizar_usuario(usuario_id, payload)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado.")

    return UsuarioOutput.from_entity(usuario)


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remover usuario")
def remover_usuario(
    usuario_id: int,
    current_user: Usuario = Depends(require_roles(RoleUsuario.ADMIN)),
    service: UsuarioService = Depends(get_usuario_service),
) -> None:
    if current_user.id == usuario_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O administrador logado nao pode remover a propria conta.",
        )

    removeu = service.remover_usuario(usuario_id)
    if not removeu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado.")
