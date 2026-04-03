from app.application.services.prediction_provider import PredictionProvider
from app.core.cache import MemoryCache
from app.domain.entities.confronto import Confronto, PrevisaoConfronto
from app.domain.entities.equipe import Equipe
from app.domain.repositories.confronto_repository import ConfrontoRepository
from app.domain.repositories.equipe_repository import EquipeRepository


class ConfrontoPredictionService:
    def __init__(
        self,
        confronto_repository: ConfrontoRepository,
        equipe_repository: EquipeRepository,
        provider: PredictionProvider,
        cache: MemoryCache,
    ) -> None:
        self.confronto_repository = confronto_repository
        self.equipe_repository = equipe_repository
        self.provider = provider
        self.cache = cache

    def gerar_e_salvar(self, confronto_id: int) -> Confronto | None:
        confronto = self.confronto_repository.obter_por_id(confronto_id)
        if confronto is None:
            return None

        try:
            participantes = self.equipe_repository.listar()
            participante_a = self._find_participante(confronto, confronto.participanteAId, confronto.equipeA, participantes)
            participante_b = self._find_participante(confronto, confronto.participanteBId, confronto.equipeB, participantes)
            historico = self.confronto_repository.listar()
            previsao = self.provider.gerar_previsao(confronto, participante_a, participante_b, historico)
        except Exception as exc:
            previsao = PrevisaoConfronto.erro_previsao(str(exc), getattr(self.provider, "model_name", None))

        confronto_atualizado = confronto.model_copy(update={"previsao": previsao})
        resultado = self.confronto_repository.atualizar(confronto_id, confronto_atualizado)
        self.cache.invalidate_prefix("confrontos:")
        self.cache.invalidate_prefix("dashboard:")
        return resultado

    def _find_participante(
        self,
        confronto: Confronto,
        participante_id: int | None,
        nome: str,
        participantes: list[Equipe],
    ) -> Equipe | None:
        if participante_id is not None:
            for participante in participantes:
                if participante.id == participante_id:
                    return participante

        for participante in participantes:
            if participante.modalidade == confronto.modalidade and participante.nome == nome:
                return participante

        return None
