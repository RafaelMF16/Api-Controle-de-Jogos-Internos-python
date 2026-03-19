from abc import ABC, abstractmethod

from app.domain.entities.confronto import Confronto


class ConfrontoRepository(ABC):
    @abstractmethod
    def listar(self) -> list[Confronto]:
        raise NotImplementedError

    @abstractmethod
    def obter_por_id(self, confronto_id: int) -> Confronto | None:
        raise NotImplementedError

    @abstractmethod
    def criar(self, confronto: Confronto) -> Confronto:
        raise NotImplementedError

    @abstractmethod
    def atualizar(self, confronto_id: int, confronto: Confronto) -> Confronto | None:
        raise NotImplementedError

    @abstractmethod
    def remover(self, confronto_id: int) -> bool:
        raise NotImplementedError
