from abc import ABC, abstractmethod

from app.domain.entities.confronto import Confronto, PrevisaoConfronto
from app.domain.entities.equipe import Equipe


class PredictionProvider(ABC):
    @abstractmethod
    def gerar_previsao(
        self,
        confronto: Confronto,
        participante_a: Equipe | None,
        participante_b: Equipe | None,
        historico: list[Confronto],
    ) -> PrevisaoConfronto:
        raise NotImplementedError
