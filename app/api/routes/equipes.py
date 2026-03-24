from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_equipe_service, require_roles
from app.application.dtos.equipe_dto import EquipeInput
from app.application.services.equipe_service import EquipeService
from app.domain.entities.equipe import Equipe
from app.domain.entities.usuario import RoleUsuario, Usuario

router = APIRouter(prefix="/equipes", tags=["Equipes"])


# Retorna todas as equipes cadastradas para popular listagens, cards e formularios do front-end.
@router.get("", response_model=list[Equipe], summary="Listar equipes")
def listar_equipes(service: EquipeService = Depends(get_equipe_service)) -> list[Equipe]:
    return service.listar_equipes()


# Busca os detalhes completos de uma equipe especifica, incluindo os membros associados.
@router.get("/{equipe_id}", response_model=Equipe, summary="Obter equipe por id")
def obter_equipe(equipe_id: int, service: EquipeService = Depends(get_equipe_service)) -> Equipe:
    equipe = service.obter_equipe(equipe_id)
    if equipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipe nao encontrada.")
    return equipe


# Cria uma nova equipe com a mesma estrutura esperada pelo front Angular.
@router.post("", response_model=Equipe, status_code=status.HTTP_201_CREATED, summary="Criar equipe")
def criar_equipe(
    payload: EquipeInput,
    _: Usuario = Depends(require_roles(RoleUsuario.ADMIN)),
    service: EquipeService = Depends(get_equipe_service),
) -> Equipe:
    return service.criar_equipe(payload)


# Atualiza uma equipe existente mantendo o contrato de dados usado pela tela de equipes.
@router.put("/{equipe_id}", response_model=Equipe, summary="Atualizar equipe")
def atualizar_equipe(
    equipe_id: int,
    payload: EquipeInput,
    current_user: Usuario = Depends(get_current_user),
    service: EquipeService = Depends(get_equipe_service),
) -> Equipe:
    if current_user.role not in {RoleUsuario.ADMIN, RoleUsuario.CAPITAO}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voce nao tem permissao para esta acao.")

    if current_user.role == RoleUsuario.CAPITAO and current_user.equipeId != equipe_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Capitao so pode editar a propria equipe.")

    equipe_atualizada = service.atualizar_equipe(equipe_id, payload)
    if equipe_atualizada is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipe nao encontrada.")
    return equipe_atualizada


# Remove uma equipe cadastrada da colecao persistida no Firestore.
@router.delete("/{equipe_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remover equipe")
def remover_equipe(
    equipe_id: int,
    _: Usuario = Depends(require_roles(RoleUsuario.ADMIN)),
    service: EquipeService = Depends(get_equipe_service),
) -> None:
    removeu = service.remover_equipe(equipe_id)
    if not removeu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipe nao encontrada.")
