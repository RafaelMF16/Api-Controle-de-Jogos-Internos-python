from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_formato_service, get_ranking_service, require_roles
from app.application.dtos.formato_modalidade_dto import FormatoModalidadeInput, RankingResponse
from app.application.services.formato_modalidade_service import FormatoModalidadeService
from app.application.services.ranking_service import RankingService
from app.domain.entities.equipe import ModalidadeEquipe
from app.domain.entities.formato_modalidade import FormatoModalidade
from app.domain.entities.usuario import RoleUsuario, Usuario

router = APIRouter(tags=["Formatos e Ranking"])


@router.get("/formatos", response_model=list[FormatoModalidade], summary="Listar formatos configurados")
def listar_formatos(service: FormatoModalidadeService = Depends(get_formato_service)) -> list[FormatoModalidade]:
    return service.listar()


@router.get("/formatos/{modalidade}", response_model=FormatoModalidade, summary="Obter formato de uma modalidade")
def obter_formato(
    modalidade: ModalidadeEquipe,
    service: FormatoModalidadeService = Depends(get_formato_service),
) -> FormatoModalidade:
    formato = service.obter(modalidade)
    if formato is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formato não configurado para esta modalidade.")
    return formato


@router.put("/formatos/{modalidade}", response_model=FormatoModalidade, summary="Salvar formato de uma modalidade")
def salvar_formato(
    modalidade: ModalidadeEquipe,
    payload: FormatoModalidadeInput,
    _: Usuario = Depends(require_roles(RoleUsuario.ADMIN)),
    service: FormatoModalidadeService = Depends(get_formato_service),
) -> FormatoModalidade:
    return service.salvar(modalidade, payload)


@router.delete("/formatos/{modalidade}", status_code=status.HTTP_204_NO_CONTENT, summary="Remover formato de uma modalidade")
def remover_formato(
    modalidade: ModalidadeEquipe,
    _: Usuario = Depends(require_roles(RoleUsuario.ADMIN)),
    service: FormatoModalidadeService = Depends(get_formato_service),
) -> None:
    removeu = service.remover(modalidade)
    if not removeu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formato não configurado para esta modalidade.")


@router.get("/ranking/{modalidade}", response_model=RankingResponse, summary="Obter ranking de uma modalidade")
def obter_ranking(
    modalidade: ModalidadeEquipe,
    service: RankingService = Depends(get_ranking_service),
) -> RankingResponse:
    ranking = service.calcular_ranking(modalidade)
    if ranking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formato não configurado para esta modalidade.")
    return ranking
