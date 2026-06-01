import math
import random

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_confronto_generation_service, get_confronto_repository, get_equipe_repository, get_formato_service, get_ranking_service, require_roles
from app.application.dtos.formato_modalidade_dto import FormatoModalidadeInput, RankingResponse
from app.application.services.confronto_generation_service import ConfrontoGenerationService
from app.application.services.formato_modalidade_service import FormatoModalidadeService
from app.application.services.ranking_service import RankingService
from app.domain.entities.equipe import ModalidadeEquipe
from app.domain.entities.formato_modalidade import FormatoModalidade, GrupoConfig, PontuacaoConfig, TipoFormato
from app.domain.entities.usuario import RoleUsuario, Usuario
from app.domain.repositories.confronto_repository import ConfrontoRepository
from app.domain.repositories.equipe_repository import EquipeRepository

_NOMES_FASES: dict[int, list[str]] = {
    1: ["Final"],
    2: ["Semifinal", "Final"],
    3: ["Quartas de final", "Semifinal", "Final"],
    4: ["Oitavas de final", "Quartas de final", "Semifinal", "Final"],
    5: ["Rodada de 32", "Oitavas de final", "Quartas de final", "Semifinal", "Final"],
}


def _calcular_fases(n_equipes: int) -> list[str]:
    n_rounds = max(1, math.ceil(math.log2(n_equipes)))
    return _NOMES_FASES.get(n_rounds, [f"Fase {n_rounds - i}" for i in range(n_rounds)])


def _is_potencia_de_dois(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def _calcular_grupos_automatico(n: int, equipes: list[str]) -> tuple[list[GrupoConfig], list[str]]:
    # n_grupos must be a power of 2 so the knockout phases work cleanly
    if n <= 8:
        n_grupos = 2
    elif n <= 24:
        n_grupos = 4
    else:
        n_grupos = 8

    letras = "ABCDEFGH"
    nomes_grupos = [f"Grupo {letras[i]}" for i in range(n_grupos)]

    # 2 qualifiers per group → n_grupos*2 teams in knockout (always a power of 2)
    knockout_rounds = int(math.log2(n_grupos * 2))
    fases_knockout = _NOMES_FASES.get(knockout_rounds, [f"Fase {knockout_rounds - i}" for i in range(knockout_rounds)])

    equipes_embaralhadas = list(equipes)
    random.shuffle(equipes_embaralhadas)
    # Interleaved distribution keeps group sizes balanced
    grupos = [GrupoConfig(nome=nome, equipes=equipes_embaralhadas[i::n_grupos]) for i, nome in enumerate(nomes_grupos)]

    return grupos, fases_knockout


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
    gen_service: ConfrontoGenerationService = Depends(get_confronto_generation_service),
) -> FormatoModalidade:
    salvo = service.salvar(modalidade, payload)
    try:
        gen_service.gerar_confrontos(salvo)
    except ValueError:
        pass
    return salvo


@router.delete("/formatos/{modalidade}", status_code=status.HTTP_204_NO_CONTENT, summary="Remover formato de uma modalidade")
def remover_formato(
    modalidade: ModalidadeEquipe,
    _: Usuario = Depends(require_roles(RoleUsuario.ADMIN)),
    service: FormatoModalidadeService = Depends(get_formato_service),
) -> None:
    removeu = service.remover(modalidade)
    if not removeu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formato não configurado para esta modalidade.")


@router.post("/formatos/{modalidade}/finalizar-grupos", summary="Finalizar fase de grupos e criar confrontos eliminatórios")
def finalizar_grupos(
    modalidade: ModalidadeEquipe,
    _: Usuario = Depends(require_roles(RoleUsuario.ADMIN)),
    formato_service: FormatoModalidadeService = Depends(get_formato_service),
    ranking_service: RankingService = Depends(get_ranking_service),
    gen_service: ConfrontoGenerationService = Depends(get_confronto_generation_service),
) -> dict:
    formato = formato_service.obter(modalidade)
    if formato is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formato não configurado para esta modalidade.")

    ranking = ranking_service.calcular_ranking(modalidade)
    if ranking is None or not ranking.grupos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato não é do tipo grupos+mata-mata ou não possui grupos.")

    try:
        criados = gen_service.finalizar_grupos(formato, ranking.grupos)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return {"confrontos_criados": criados}


@router.post("/formatos/{modalidade}/gerar-automatico", summary="Gerar formato automaticamente com base nas equipes cadastradas")
def gerar_automatico(
    modalidade: ModalidadeEquipe,
    tipo: TipoFormato = Query(default=TipoFormato.MATA_MATA),
    _: Usuario = Depends(require_roles(RoleUsuario.ADMIN)),
    formato_service: FormatoModalidadeService = Depends(get_formato_service),
    equipe_repo: EquipeRepository = Depends(get_equipe_repository),
    confronto_repo: ConfrontoRepository = Depends(get_confronto_repository),
    gen_service: ConfrontoGenerationService = Depends(get_confronto_generation_service),
) -> dict:
    # Reset: apagar confrontos e formato existentes antes de recriar
    existentes = confronto_repo.listar_paginado(
        equipe=None, modalidade=modalidade.value, status=None, limit=500, cursor=None,
    )
    for c in existentes.items:
        confronto_repo.remover(c.id)
    if existentes.items:
        gen_service.cache.invalidate_prefix("confrontos:")
        gen_service.cache.invalidate_prefix("ranking:")

    formato_service.remover(modalidade)

    equipes_pag = equipe_repo.listar_paginado(
        categoria=None, modalidade=modalidade.value,
        nome_exato=None, usuario_id=None, limit=200, cursor=None,
    )
    nomes = [e.nome for e in equipes_pag.items]
    n = len(nomes)
    if n < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"São necessárias ao menos 2 equipes cadastradas. Encontrada(s): {n}.",
        )

    if tipo == TipoFormato.MATA_MATA:
        if not _is_potencia_de_dois(n):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Mata-mata requer um número de equipes que seja potência de 2 "
                    f"(2, 4, 8, 16, 32...). Equipes cadastradas: {n}. "
                    "Considere usar Liga ou Grupos + Mata-mata."
                ),
            )
        fases = _calcular_fases(n)
        payload = FormatoModalidadeInput(tipo=TipoFormato.MATA_MATA, fases=fases, grupos=[], pontuacao=PontuacaoConfig())
        salvo = formato_service.salvar(modalidade, payload)
        criados = gen_service.gerar_confrontos(salvo)
        return {"confrontos_criados": criados, "fases": fases}

    if tipo == TipoFormato.LIGA:
        payload = FormatoModalidadeInput(tipo=TipoFormato.LIGA, fases=[], grupos=[], pontuacao=PontuacaoConfig())
        salvo = formato_service.salvar(modalidade, payload)
        criados = gen_service.gerar_confrontos(salvo)
        return {"confrontos_criados": criados, "fases": []}

    # GRUPOS_MATA_MATA
    grupos, fases_knockout = _calcular_grupos_automatico(n, nomes)
    payload = FormatoModalidadeInput(
        tipo=TipoFormato.GRUPOS_MATA_MATA,
        fases=fases_knockout,
        grupos=grupos,
        pontuacao=PontuacaoConfig(),
    )
    salvo = formato_service.salvar(modalidade, payload)
    criados = gen_service.gerar_confrontos(salvo)
    return {"confrontos_criados": criados, "fases": fases_knockout}


@router.get("/ranking/{modalidade}", response_model=RankingResponse, summary="Obter ranking de uma modalidade")
def obter_ranking(
    modalidade: ModalidadeEquipe,
    service: RankingService = Depends(get_ranking_service),
) -> RankingResponse:
    ranking = service.calcular_ranking(modalidade)
    if ranking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formato não configurado para esta modalidade.")
    return ranking
