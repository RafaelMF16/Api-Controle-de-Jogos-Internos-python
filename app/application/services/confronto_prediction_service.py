from app.application.services.prediction_provider import PredictionProvider
from app.core.cache import MemoryCache
from app.domain.entities.confronto import Confronto, PrevisaoConfronto
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
            participante_a = self._obter_participante(confronto.participanteAId, confronto.equipeA, confronto.modalidade.value)
            participante_b = self._obter_participante(confronto.participanteBId, confronto.equipeB, confronto.modalidade.value)
            historico = self.confronto_repository.listar_historico_relevante(
                modalidade=confronto.modalidade.value,
                participante_ids=[item for item in [confronto.participanteAId, confronto.participanteBId] if item],
                nomes_participantes=[confronto.equipeA, confronto.equipeB],
                limit=20,
            )
            previsao = self.provider.gerar_previsao(confronto, participante_a, participante_b, historico)
        except Exception as exc:
            previsao = PrevisaoConfronto.erro_previsao(str(exc), getattr(self.provider, "model_name", None))

        confronto_atualizado = confronto.model_copy(update={"previsao": previsao})
        resultado = self.confronto_repository.atualizar(confronto_id, confronto_atualizado)
        self.cache.invalidate_prefix("confrontos:")
        self.cache.invalidate_prefix("dashboard:")
        return resultado

    def _obter_participante(self, participante_id: int | None, nome: str, modalidade: str):
        if participante_id is not None:
            participantes = self.equipe_repository.obter_por_ids([participante_id])
            if participantes:
                return participantes[0]

        return self.equipe_repository.obter_por_nome_modalidade(nome, modalidade)
