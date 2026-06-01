import random

from app.application.dtos.formato_modalidade_dto import ClassificacaoGrupo
from app.core.cache import MemoryCache
from app.domain.entities.confronto import Confronto, PrevisaoConfronto, StatusConfronto
from app.domain.entities.equipe import ModalidadeEquipe
from app.domain.entities.formato_modalidade import FormatoModalidade, TipoFormato
from app.domain.repositories.confronto_repository import ConfrontoRepository
from app.domain.repositories.equipe_repository import EquipeRepository


class ConfrontoGenerationService:
    def __init__(
        self,
        confronto_repository: ConfrontoRepository,
        equipe_repository: EquipeRepository,
        cache: MemoryCache,
    ) -> None:
        self.confronto_repository = confronto_repository
        self.equipe_repository = equipe_repository
        self.cache = cache

    def gerar_confrontos(self, formato: FormatoModalidade) -> int:
        existentes = self.confronto_repository.listar_paginado(
            equipe=None,
            modalidade=formato.modalidade.value,
            status=None,
            limit=1,
            cursor=None,
        )
        if existentes.items:
            return 0

        if formato.tipo == TipoFormato.LIGA:
            return self._gerar_liga(formato)
        if formato.tipo == TipoFormato.MATA_MATA:
            return self._gerar_mata_mata(formato)
        return self._gerar_grupos(formato)

    def finalizar_grupos(self, formato: FormatoModalidade, grupos_classificacao: list[ClassificacaoGrupo]) -> int:
        nomes_grupos = [g.nome for g in formato.grupos]
        fases_knockout = [f for f in formato.fases if f not in nomes_grupos]
        if not fases_knockout:
            raise ValueError("Formato não possui fases de mata-mata definidas.")

        primeira_fase_knockout = fases_knockout[0]

        todos = self.confronto_repository.listar_paginado(
            equipe=None,
            modalidade=formato.modalidade.value,
            status=None,
            limit=500,
            cursor=None,
        ).items
        if any(c.fase == primeira_fase_knockout for c in todos):
            raise ValueError("Confrontos da fase eliminatória já foram criados.")

        # Cruzamento: 1º do grupo par vs 2º do grupo ímpar adjacente, e vice-versa
        n = len(grupos_classificacao)
        pares: list[tuple[str, str]] = []
        for i in range(0, n, 2):
            grupo_a = grupos_classificacao[i]
            grupo_b = grupos_classificacao[(i + 1) % n]
            nomes_a = [p.equipe for p in grupo_a.posicoes]
            nomes_b = [p.equipe for p in grupo_b.posicoes]
            if nomes_a and len(nomes_b) > 1:
                pares.append((nomes_a[0], nomes_b[1]))
            if nomes_b and len(nomes_a) > 1:
                pares.append((nomes_b[0], nomes_a[1]))

        return self._criar_confrontos(pares, formato.modalidade, fase=primeira_fase_knockout)

    def _gerar_liga(self, formato: FormatoModalidade) -> int:
        equipes = self._obter_nomes_equipes(formato.modalidade)
        pares = [
            (equipes[i], equipes[j])
            for i in range(len(equipes))
            for j in range(i + 1, len(equipes))
        ]
        return self._criar_confrontos(pares, formato.modalidade, fase=None)

    def _gerar_mata_mata(self, formato: FormatoModalidade) -> int:
        equipes = self._obter_nomes_equipes(formato.modalidade)
        if len(equipes) % 2 != 0:
            raise ValueError(
                f"Número ímpar de equipes ({len(equipes)}) para o formato mata-mata. "
                "Ajuste o número de equipes antes de salvar o formato."
            )
        random.shuffle(equipes)
        primeira_fase = formato.fases[0] if formato.fases else None
        pares = [(equipes[i], equipes[i + 1]) for i in range(0, len(equipes), 2)]
        return self._criar_confrontos(pares, formato.modalidade, fase=primeira_fase)

    def _gerar_grupos(self, formato: FormatoModalidade) -> int:
        total = 0
        for grupo in formato.grupos:
            nomes = grupo.equipes
            pares = [
                (nomes[i], nomes[j])
                for i in range(len(nomes))
                for j in range(i + 1, len(nomes))
            ]
            total += self._criar_confrontos(pares, formato.modalidade, fase=grupo.nome)
        return total

    def _criar_confrontos(
        self,
        pares: list[tuple[str, str]],
        modalidade: ModalidadeEquipe,
        fase: str | None,
    ) -> int:
        for equipe_a, equipe_b in pares:
            novo_id = self.confronto_repository.proximo_id()
            confronto = Confronto(
                id=novo_id,
                equipeA=equipe_a,
                equipeB=equipe_b,
                modalidade=modalidade,
                status=StatusConfronto.AGENDADO,
                fase=fase,
                previsao=PrevisaoConfronto.pendente(),
            )
            self.confronto_repository.criar(confronto)
        if pares:
            self.cache.invalidate_prefix("confrontos:")
            self.cache.invalidate_prefix("ranking:")
        return len(pares)

    def _obter_nomes_equipes(self, modalidade: ModalidadeEquipe) -> list[str]:
        equipes = self.equipe_repository.listar_paginado(
            categoria=None,
            modalidade=modalidade.value,
            nome_exato=None,
            usuario_id=None,
            limit=200,
            cursor=None,
        ).items
        return [e.nome for e in equipes]
