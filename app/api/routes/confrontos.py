from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_confronto_service
from app.application.dtos.confronto_dto import ConfrontoInput
from app.application.services.confronto_service import ConfrontoService
from app.domain.entities.confronto import Confronto, StatusConfronto

router = APIRouter(prefix="/confrontos", tags=["Confrontos"])


# Lista confrontos e permite filtrar por equipe, modalidade ou status para as telas do sistema.
@router.get("", response_model=list[Confronto], summary="Listar confrontos")
def listar_confrontos(
    equipe: str | None = Query(default=None),
    modalidade: str | None = Query(default=None),
    status_filtro: StatusConfronto | None = Query(default=None, alias="status"),
    service: ConfrontoService = Depends(get_confronto_service),
) -> list[Confronto]:
    return service.listar_confrontos(
        equipe=equipe,
        modalidade=modalidade,
        status=status_filtro,
    )


# Retorna apenas confrontos agendados ou ao vivo para alimentar dashboard e agenda principal.
@router.get("/proximos", response_model=list[Confronto], summary="Listar proximos confrontos")
def listar_proximos_confrontos(service: ConfrontoService = Depends(get_confronto_service)) -> list[Confronto]:
    return service.listar_proximos_confrontos()


# Busca um confronto especifico com todos os dados necessarios para edicao ou visualizacao detalhada.
@router.get("/{confronto_id}", response_model=Confronto, summary="Obter confronto por id")
def obter_confronto(confronto_id: int, service: ConfrontoService = Depends(get_confronto_service)) -> Confronto:
    confronto = service.obter_confronto(confronto_id)
    if confronto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Confronto nao encontrado.")
    return confronto


# Cria um novo confronto seguindo o mesmo formato utilizado pelo front-end Angular.
@router.post("", response_model=Confronto, status_code=status.HTTP_201_CREATED, summary="Criar confronto")
def criar_confronto(payload: ConfrontoInput, service: ConfrontoService = Depends(get_confronto_service)) -> Confronto:
    return service.criar_confronto(payload)


# Atualiza um confronto existente, incluindo placar, status e metadados exibidos na interface.
@router.put("/{confronto_id}", response_model=Confronto, summary="Atualizar confronto")
def atualizar_confronto(
    confronto_id: int,
    payload: ConfrontoInput,
    service: ConfrontoService = Depends(get_confronto_service),
) -> Confronto:
    confronto_atualizado = service.atualizar_confronto(confronto_id, payload)
    if confronto_atualizado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Confronto nao encontrado.")
    return confronto_atualizado


# Remove um confronto do armazenamento em JSON para refletir a exclusao feita no sistema.
@router.delete("/{confronto_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remover confronto")
def remover_confronto(confronto_id: int, service: ConfrontoService = Depends(get_confronto_service)) -> None:
    removeu = service.remover_confronto(confronto_id)
    if not removeu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Confronto nao encontrado.")
