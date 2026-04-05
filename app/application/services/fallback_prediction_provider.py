import logging

from app.application.services.prediction_provider import PredictionProvider
from app.domain.entities.confronto import Confronto, PrevisaoConfronto
from app.domain.entities.equipe import Equipe

logger = logging.getLogger(__name__)


class FallbackPredictionProvider(PredictionProvider):
    def __init__(self, primary: PredictionProvider, fallback: PredictionProvider) -> None:
        self.primary = primary
        self.fallback = fallback
        self.model_name = getattr(primary, "model_name", None)

    def gerar_previsao(
        self,
        confronto: Confronto,
        participante_a: Equipe | None,
        participante_b: Equipe | None,
        historico: list[Confronto],
    ) -> PrevisaoConfronto:
        try:
            return self.primary.gerar_previsao(confronto, participante_a, participante_b, historico)
        except Exception as exc:
            logger.exception("Falha ao gerar previsao com o provedor principal. Usando fallback. Erro: %s", exc)
            return self.fallback.gerar_previsao(confronto, participante_a, participante_b, historico)
