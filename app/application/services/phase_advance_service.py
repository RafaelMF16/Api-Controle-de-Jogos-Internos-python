from app.application.services.confronto_generation_service import ConfrontoGenerationService
from app.domain.entities.confronto import Confronto, StatusConfronto
from app.domain.repositories.confronto_repository import ConfrontoRepository
from app.domain.repositories.formato_modalidade_repository import FormatoModalidadeRepository


class PhaseAdvanceService:
    def __init__(
        self,
        confronto_repository: ConfrontoRepository,
        formato_repository: FormatoModalidadeRepository,
        generation_service: ConfrontoGenerationService,
    ) -> None:
        self.confronto_repository = confronto_repository
        self.formato_repository = formato_repository
        self.generation_service = generation_service

    def tentar_avancar_fase(self, confronto_encerrado: Confronto) -> None:
        if not confronto_encerrado.fase:
            return

        todos = self.confronto_repository.listar_paginado(
            equipe=None,
            modalidade=confronto_encerrado.modalidade.value,
            status=None,
            limit=500,
            cursor=None,
        ).items

        fase_atual = confronto_encerrado.fase
        confrontos_fase = [c for c in todos if c.fase == fase_atual]

        if not all(c.status == StatusConfronto.ENCERRADO for c in confrontos_fase):
            return

        formato = self.formato_repository.obter(confronto_encerrado.modalidade)
        if formato is None:
            return

        # Só avança fases do mata-mata (fases definidas em formato.fases)
        # Fases de grupo (grupos+mata-mata) são tratadas pelo endpoint finalizar-grupos
        if fase_atual not in formato.fases:
            return

        idx = formato.fases.index(fase_atual)
        if idx + 1 >= len(formato.fases):
            return  # Era a fase final

        proxima_fase = formato.fases[idx + 1]

        if any(c.fase == proxima_fase for c in todos):
            return  # Confrontos da próxima fase já existem

        confrontos_fase_ordenados = sorted(confrontos_fase, key=lambda c: c.id)
        vencedores = [self._determinar_vencedor(c) for c in confrontos_fase_ordenados]
        vencedores = [v for v in vencedores if v]

        if len(vencedores) != len(confrontos_fase_ordenados):
            return  # Algum confronto sem vencedor determinável (empate sem critério)

        if len(vencedores) % 2 != 0:
            return

        pares = [(vencedores[i], vencedores[i + 1]) for i in range(0, len(vencedores), 2)]
        self.generation_service._criar_confrontos(pares, confronto_encerrado.modalidade, fase=proxima_fase)

    def _determinar_vencedor(self, confronto: Confronto) -> str | None:
        if confronto.vencedor:
            return confronto.vencedor
        if confronto.golsA is not None and confronto.golsB is not None:
            if confronto.golsA > confronto.golsB:
                return confronto.equipeA
            if confronto.golsB > confronto.golsA:
                return confronto.equipeB
        return None
