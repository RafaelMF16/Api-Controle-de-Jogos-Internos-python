from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_current_user, get_equipe_service, get_usuario_service, require_roles
from app.application.dtos.cursor_pagination_dto import CursorPaginatedResponse
from app.application.dtos.equipe_dto import EquipeInput
from app.application.services.equipe_service import EquipeService
from app.application.services.usuario_service import UsuarioService
from app.domain.entities.equipe import Equipe, ModalidadeEquipe
from app.domain.entities.usuario import RoleUsuario, Usuario

router = APIRouter(prefix="/equipes", tags=["Equipes"])


@router.get("", response_model=CursorPaginatedResponse[Equipe], summary="Listar equipes")
def listar_equipes(
    categoria: str | None = Query(default=None, pattern="^(coletivo|individual)$"),
    cursor: str | None = Query(default=None),
    page_size: int = Query(default=10, ge=1, le=50),
    service: EquipeService = Depends(get_equipe_service),
) -> CursorPaginatedResponse[Equipe]:
    return service.listar_equipes_paginado(categoria=categoria, limit=page_size, cursor=cursor)


@router.get("/{equipe_id}", response_model=Equipe, summary="Obter equipe por id")
def obter_equipe(equipe_id: int, service: EquipeService = Depends(get_equipe_service)) -> Equipe:
    equipe = service.obter_equipe(equipe_id)
    if equipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cadastro nao encontrado.")
    return equipe


@router.post("", response_model=Equipe, status_code=status.HTTP_201_CREATED, summary="Criar equipe")
def criar_equipe(
    payload: EquipeInput,
    current_user: Usuario = Depends(get_current_user),
    service: EquipeService = Depends(get_equipe_service),
    usuario_service: UsuarioService = Depends(get_usuario_service),
) -> Equipe:
    if payload.modalidade == ModalidadeEquipe.NATACAO:
        if current_user.role not in {RoleUsuario.ADMIN, RoleUsuario.VISITANTE, RoleUsuario.CAPITAO}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voce nao tem permissao para esta acao.")

        if current_user.role in {RoleUsuario.VISITANTE, RoleUsuario.CAPITAO}:
            if not current_user.curso or not current_user.periodo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Complete seu cadastro com curso e periodo para se inscrever.",
                )

            existente = service.obter_inscricao_individual(current_user.id, payload.modalidade)
            if existente is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Voce ja possui inscricao nessa modalidade.",
                )

            payload = payload.model_copy(
                update={
                    "nome": current_user.nome,
                    "curso": current_user.curso,
                    "periodo": current_user.periodo,
                    "usuarioId": current_user.id,
                    "responsavel": None,
                    "membros": [],
                }
            )

        return service.criar_equipe(payload)

    if current_user.role not in {RoleUsuario.ADMIN, RoleUsuario.CAPITAO}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voce nao tem permissao para esta acao.")

    if current_user.role == RoleUsuario.CAPITAO and current_user.equipeId is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Capitao so pode cadastrar uma equipe.")

    payload_ajustado = payload.model_copy(
        update={
            "responsavel": current_user.nome,
            "periodo": current_user.periodo if current_user.role == RoleUsuario.CAPITAO and current_user.periodo else payload.periodo,
            "usuarioId": None,
        }
    )
    equipe = service.criar_equipe(payload_ajustado)

    if current_user.role == RoleUsuario.CAPITAO:
        usuario_service.vincular_equipe(current_user.id, equipe.id)

    return equipe


@router.put("/{equipe_id}", response_model=Equipe, summary="Atualizar equipe")
def atualizar_equipe(
    equipe_id: int,
    payload: EquipeInput,
    current_user: Usuario = Depends(get_current_user),
    service: EquipeService = Depends(get_equipe_service),
) -> Equipe:
    equipe_atual = service.obter_equipe(equipe_id)
    if equipe_atual is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cadastro nao encontrado.")

    if equipe_atual.modalidade == ModalidadeEquipe.NATACAO:
        if current_user.role in {RoleUsuario.VISITANTE, RoleUsuario.CAPITAO}:
            if equipe_atual.usuarioId != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Voce so pode editar a propria inscricao.",
                )

            payload = payload.model_copy(
                update={
                    "nome": current_user.nome,
                    "curso": current_user.curso,
                    "periodo": current_user.periodo,
                    "usuarioId": current_user.id,
                    "responsavel": None,
                    "membros": [],
                }
            )
        elif current_user.role != RoleUsuario.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voce nao tem permissao para esta acao.")
    else:
        if current_user.role not in {RoleUsuario.ADMIN, RoleUsuario.CAPITAO}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voce nao tem permissao para esta acao.")

        if current_user.role == RoleUsuario.CAPITAO and current_user.equipeId != equipe_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Capitao so pode editar a propria equipe.")

        payload = payload.model_copy(
            update={
                "responsavel": equipe_atual.responsavel,
                "usuarioId": None,
            }
        )

    if payload.modalidade == ModalidadeEquipe.NATACAO and payload.usuarioId is not None:
        existente = service.obter_inscricao_individual(payload.usuarioId, payload.modalidade)
        if existente is not None and existente.id != equipe_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ja existe uma inscricao nessa modalidade para este usuario.",
            )

    equipe_atualizada = service.atualizar_equipe(equipe_id, payload)
    if equipe_atualizada is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cadastro nao encontrado.")
    return equipe_atualizada


@router.delete("/{equipe_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remover equipe")
def remover_equipe(
    equipe_id: int,
    _: Usuario = Depends(require_roles(RoleUsuario.ADMIN)),
    service: EquipeService = Depends(get_equipe_service),
) -> None:
    removeu = service.remover_equipe(equipe_id)
    if not removeu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cadastro nao encontrado.")
