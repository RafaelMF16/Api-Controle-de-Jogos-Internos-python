from abc import ABC, abstractmethod

from app.domain.entities.equipe import Equipe


class EquipeRepository(ABC):
    @abstractmethod
    def listar(self) -> list[Equipe]:
        raise NotImplementedError

    @abstractmethod
    def obter_por_id(self, equipe_id: int) -> Equipe | None:
        raise NotImplementedError

    @abstractmethod
    def criar(self, equipe: Equipe) -> Equipe:
        raise NotImplementedError

    @abstractmethod
    def atualizar(self, equipe_id: int, equipe: Equipe) -> Equipe | None:
        raise NotImplementedError

    @abstractmethod
    def remover(self, equipe_id: int) -> bool:
        raise NotImplementedError
