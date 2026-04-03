from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_confronto_service, require_roles
from app.application.dtos.confronto_dto import ConfrontoInput
from app.application.dtos.pagination_dto import PaginatedResponse, build_paginated_response
from app.application.services.confronto_service import ConfrontoService
from app.domain.entities.confronto import Confronto, StatusConfronto
from app.domain.entities.usuario import RoleUsuario, Usuario

router = APIRouter(prefix="/confrontos", tags=["Confrontos"])


@router.get("", response_model=PaginatedResponse[Confronto], summary="Listar confrontos")
def listar_confrontos(
    busca: str | None = Query(default=None),
    equipe: str | None = Query(default=None),
    modalidade: str | None = Query(default=None),
    status_filtro: StatusConfronto | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=200),
    service: ConfrontoService = Depends(get_confronto_service),
) -> PaginatedResponse[Confronto]:
    confrontos = service.listar_confrontos(
        busca=busca,
        equipe=equipe,
        modalidade=modalidade,
        status=status_filtro,
    )
    return build_paginated_response(confrontos, page, page_size)


@router.get("/proximos", response_model=list[Confronto], summary="Listar próximos confrontos")
def listar_proximos_confrontos(service: ConfrontoService = Depends(get_confronto_service)) -> list[Confronto]:
    return service.listar_proximos_confrontos()


@router.get("/{confronto_id}", response_model=Confronto, summary="Obter confronto por id")
def obter_confronto(confronto_id: int, service: ConfrontoService = Depends(get_confronto_service)) -> Confronto:
    confronto = service.obter_confronto(confronto_id)
    if confronto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Confronto não encontrado.")
    return confronto


@router.post("", response_model=Confronto, status_code=status.HTTP_201_CREATED, summary="Criar confronto")
def criar_confronto(
    payload: ConfrontoInput,
    _: Usuario = Depends(require_roles(RoleUsuario.ADMIN, RoleUsuario.JUIZ)),
    service: ConfrontoService = Depends(get_confronto_service),
) -> Confronto:
    return service.criar_confronto(payload)


@router.put("/{confronto_id}", response_model=Confronto, summary="Atualizar confronto")
def atualizar_confronto(
    confronto_id: int,
    payload: ConfrontoInput,
    _: Usuario = Depends(require_roles(RoleUsuario.ADMIN, RoleUsuario.JUIZ)),
    service: ConfrontoService = Depends(get_confronto_service),
) -> Confronto:
    confronto_atualizado = service.atualizar_confronto(confronto_id, payload)
    if confronto_atualizado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Confronto não encontrado.")
    return confronto_atualizado


@router.delete("/{confronto_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remover confronto")
def remover_confronto(
    confronto_id: int,
    _: Usuario = Depends(require_roles(RoleUsuario.ADMIN, RoleUsuario.JUIZ)),
    service: ConfrontoService = Depends(get_confronto_service),
) -> None:
    removeu = service.remover_confronto(confronto_id)
    if not removeu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Confronto não encontrado.")
