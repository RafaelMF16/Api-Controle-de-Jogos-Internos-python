from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_current_user, get_equipe_service, get_usuario_service, require_roles
from app.application.dtos.cursor_pagination_dto import CursorPaginatedResponse
from app.application.dtos.equipe_dto import EquipeInput, MembroInput
from app.application.services.equipe_service import EquipeService
from app.application.services.usuario_service import UsuarioService
from app.domain.entities.equipe import CAPITAO_FUNCAO, Equipe, ModalidadeEquipe, eh_membro_capitao
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

    payload_ajustado = _normalizar_payload_coletivo(payload, current_user)
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

        payload = _normalizar_payload_coletivo(payload, current_user, equipe_atual)

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


def _normalizar_payload_coletivo(payload: EquipeInput, current_user: Usuario, equipe_atual: Equipe | None = None) -> EquipeInput:
    membros_normalizados = list(payload.membros)

    if current_user.role == RoleUsuario.CAPITAO:
        if not current_user.curso or not current_user.periodo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Complete seu cadastro com curso e periodo para cadastrar a equipe.",
            )

        membros_normalizados = _garantir_capitao_logado(membros_normalizados, current_user)
        return payload.model_copy(
            update={
                "curso": current_user.curso,
                "periodo": current_user.periodo,
                "responsavel": current_user.nome,
                "usuarioId": None,
                "membros": membros_normalizados,
            }
        )

    membros_normalizados = _garantir_um_capitao(membros_normalizados, equipe_atual)
    capitao = next((membro for membro in membros_normalizados if eh_membro_capitao(_to_membro_entity(membro))), None)
    responsavel = capitao.nome if capitao is not None else payload.responsavel

    return payload.model_copy(
        update={
            "responsavel": responsavel,
            "usuarioId": None,
            "membros": membros_normalizados,
        }
    )


def _garantir_capitao_logado(membros: list[MembroInput], current_user: Usuario) -> list[MembroInput]:
    membros_sem_capitao_logado = [
        membro for membro in membros
        if not ((membro.usuarioId == current_user.id) or ((membro.funcao or "").strip().lower() == CAPITAO_FUNCAO.lower()))
    ]

    capitao_existente = next((membro for membro in membros if membro.usuarioId == current_user.id), None)
    habilidades = capitao_existente.habilidades if capitao_existente is not None else []

    capitao = MembroInput(
        id=capitao_existente.id if capitao_existente else None,
        nome=current_user.nome,
        habilidades=habilidades,
        funcao=CAPITAO_FUNCAO,
        usuarioId=current_user.id,
    )
    return [capitao, *membros_sem_capitao_logado]


def _garantir_um_capitao(membros: list[MembroInput], equipe_atual: Equipe | None) -> list[MembroInput]:
    membros_normalizados = list(membros)

    if not any((membro.funcao or "").strip().lower() == CAPITAO_FUNCAO.lower() for membro in membros_normalizados):
        if equipe_atual is not None:
            capitao_atual = next((membro for membro in equipe_atual.membros if eh_membro_capitao(membro)), None)
            if capitao_atual is not None:
                membros_normalizados.insert(
                    0,
                    MembroInput(
                        id=capitao_atual.id,
                        nome=capitao_atual.nome,
                        habilidades=capitao_atual.habilidades,
                        funcao=capitao_atual.funcao,
                        usuarioId=capitao_atual.usuarioId,
                    )
                )
                return membros_normalizados

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Equipes coletivas precisam ter um membro com funcao de Capitao.",
        )

    return membros_normalizados


def _to_membro_entity(membro: MembroInput):
    from app.domain.entities.equipe import Membro

    return Membro(
        id=membro.id or 0,
        nome=membro.nome,
        habilidades=membro.habilidades,
        funcao=membro.funcao,
        usuarioId=membro.usuarioId,
    )
