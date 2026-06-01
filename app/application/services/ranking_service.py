from app.application.dtos.formato_modalidade_dto import (
    BracketConfronto,
    ClassificacaoGrupo,
    PosicaoClassificacao,
    RankingResponse,
)
from app.core.cache import MemoryCache
from app.core.config import Settings
from app.domain.entities.confronto import Confronto, StatusConfronto
from app.domain.entities.equipe import ModalidadeEquipe
from app.domain.entities.formato_modalidade import FormatoModalidade, TipoFormato
from app.domain.repositories.confronto_repository import ConfrontoRepository
from app.domain.repositories.equipe_repository import EquipeRepository
from app.domain.repositories.formato_modalidade_repository import FormatoModalidadeRepository


class RankingService:
    def __init__(
        self,
        formato_repository: FormatoModalidadeRepository,
        confronto_repository: ConfrontoRepository,
        equipe_repository: EquipeRepository,
        cache: MemoryCache,
        settings: Settings,
    ) -> None:
        self.formato_repository = formato_repository
        self.confronto_repository = confronto_repository
        self.equipe_repository = equipe_repository
        self.cache = cache
        self.settings = settings

    def calcular_ranking(self, modalidade: ModalidadeEquipe) -> RankingResponse | None:
        formato = self.formato_repository.obter(modalidade)
        if formato is None:
            return None

        return self.cache.get_or_set(
            f"ranking:{modalidade.value}",
            self.settings.data_cache_ttl_seconds,
            lambda: self._computar(formato),
        )

    def _computar(self, formato: FormatoModalidade) -> RankingResponse:
        confrontos = self.confronto_repository.listar_paginado(
            equipe=None,
            modalidade=formato.modalidade.value,
            status=None,
            limit=500,
            cursor=None,
        ).items

        if formato.tipo == TipoFormato.LIGA:
            return self._calcular_liga(formato, confrontos)
        if formato.tipo == TipoFormato.MATA_MATA:
            return self._calcular_mata_mata(formato, confrontos)
        return self._calcular_grupos_mata_mata(formato, confrontos)

    def _calcular_liga(self, formato: FormatoModalidade, confrontos: list[Confronto]) -> RankingResponse:
        encerrados = [c for c in confrontos if c.status == StatusConfronto.ENCERRADO]
        todas_equipes = self.equipe_repository.listar_paginado(
            categoria=None,
            modalidade=formato.modalidade.value,
            nome_exato=None,
            usuario_id=None,
            limit=200,
            cursor=None,
        ).items
        nomes_equipes = [e.nome for e in todas_equipes]
        classificacao = self._calcular_classificacao(encerrados, formato, equipes_fixas=nomes_equipes)
        return RankingResponse(
            tipo=TipoFormato.LIGA,
            modalidade=formato.modalidade,
            pontuacao=formato.pontuacao,
            classificacao=classificacao,
        )

    def _calcular_mata_mata(self, formato: FormatoModalidade, confrontos: list[Confronto]) -> RankingResponse:
        confrontos_por_fase = self._agrupar_por_fase(confrontos, formato.fases)
        return RankingResponse(
            tipo=TipoFormato.MATA_MATA,
            modalidade=formato.modalidade,
            fases=formato.fases,
            confrontosPorFase=confrontos_por_fase,
        )

    def _calcular_grupos_mata_mata(self, formato: FormatoModalidade, confrontos: list[Confronto]) -> RankingResponse:
        nomes_grupos = [g.nome for g in formato.grupos]
        grupos_resultado: list[ClassificacaoGrupo] = []
        for grupo in formato.grupos:
            confrontos_grupo = [c for c in confrontos if c.fase == grupo.nome and c.status == StatusConfronto.ENCERRADO]
            posicoes = self._calcular_classificacao(confrontos_grupo, formato, equipes_fixas=grupo.equipes)
            grupos_resultado.append(ClassificacaoGrupo(nome=grupo.nome, posicoes=posicoes))

        fases_knockout = [f for f in formato.fases if f not in nomes_grupos]
        confrontos_por_fase = self._agrupar_por_fase(confrontos, fases_knockout)

        return RankingResponse(
            tipo=TipoFormato.GRUPOS_MATA_MATA,
            modalidade=formato.modalidade,
            pontuacao=formato.pontuacao,
            grupos=grupos_resultado,
            fases=fases_knockout,
            confrontosPorFase=confrontos_por_fase,
        )

    def _calcular_classificacao(
        self,
        confrontos: list[Confronto],
        formato: FormatoModalidade,
        equipes_fixas: list[str] | None = None,
    ) -> list[PosicaoClassificacao]:
        pts_v = formato.pontuacao.vitoria
        pts_e = formato.pontuacao.empate
        pts_d = formato.pontuacao.derrota

        stats: dict[str, dict] = {}

        def _garantir(nome: str) -> None:
            if nome not in stats:
                stats[nome] = {"j": 0, "v": 0, "e": 0, "d": 0, "gp": 0, "gc": 0, "pts": 0}

        if equipes_fixas:
            for eq in equipes_fixas:
                _garantir(eq)

        for c in confrontos:
            _garantir(c.equipeA)
            _garantir(c.equipeB)
            s_a = stats[c.equipeA]
            s_b = stats[c.equipeB]
            s_a["j"] += 1
            s_b["j"] += 1

            if c.vencedor:
                if c.vencedor == c.equipeA:
                    s_a["v"] += 1
                    s_a["pts"] += pts_v
                    s_b["d"] += 1
                    s_b["pts"] += pts_d
                elif c.vencedor == c.equipeB:
                    s_b["v"] += 1
                    s_b["pts"] += pts_v
                    s_a["d"] += 1
                    s_a["pts"] += pts_d
                else:
                    s_a["e"] += 1
                    s_a["pts"] += pts_e
                    s_b["e"] += 1
                    s_b["pts"] += pts_e
            elif c.golsA is not None and c.golsB is not None:
                s_a["gp"] += c.golsA
                s_a["gc"] += c.golsB
                s_b["gp"] += c.golsB
                s_b["gc"] += c.golsA
                if c.golsA > c.golsB:
                    s_a["v"] += 1
                    s_a["pts"] += pts_v
                    s_b["d"] += 1
                    s_b["pts"] += pts_d
                elif c.golsB > c.golsA:
                    s_b["v"] += 1
                    s_b["pts"] += pts_v
                    s_a["d"] += 1
                    s_a["pts"] += pts_d
                else:
                    s_a["e"] += 1
                    s_a["pts"] += pts_e
                    s_b["e"] += 1
                    s_b["pts"] += pts_e

        ordenado = sorted(
            stats.items(),
            key=lambda item: (
                -item[1]["pts"],
                -(item[1]["gp"] - item[1]["gc"]),
                -item[1]["gp"],
                item[0],
            ),
        )

        return [
            PosicaoClassificacao(
                posicao=i + 1,
                equipe=nome,
                jogos=s["j"],
                vitorias=s["v"],
                empates=s["e"],
                derrotas=s["d"],
                golsPro=s["gp"],
                golsContra=s["gc"],
                saldoGols=s["gp"] - s["gc"],
                pontos=s["pts"],
            )
            for i, (nome, s) in enumerate(ordenado)
        ]

    def _agrupar_por_fase(
        self,
        confrontos: list[Confronto],
        fases: list[str],
    ) -> dict[str, list[BracketConfronto]]:
        resultado: dict[str, list[BracketConfronto]] = {fase: [] for fase in fases}
        for c in confrontos:
            if c.fase and c.fase in resultado:
                resultado[c.fase].append(
                    BracketConfronto(
                        confrontoId=c.id,
                        equipeA=c.equipeA,
                        equipeB=c.equipeB,
                        golsA=c.golsA,
                        golsB=c.golsB,
                        vencedor=c.vencedor,
                        status=c.status,
                    )
                )
        return resultado
