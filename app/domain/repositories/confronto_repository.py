from abc import ABC, abstractmethod

from app.application.dtos.cursor_pagination_dto import CursorPaginatedResponse
from app.domain.entities.confronto import Confronto
from app.domain.entities.confronto import StatusConfronto


class ConfrontoRepository(ABC):
    @abstractmethod
    def listar(self) -> list[Confronto]:
        raise NotImplementedError

    @abstractmethod
    def listar_paginado(
        self,
        *,
        equipe: str | None,
        modalidade: str | None,
        status: StatusConfronto | None,
        limit: int,
        cursor: str | None,
    ) -> CursorPaginatedResponse[Confronto]:
        raise NotImplementedError

    @abstractmethod
    def obter_por_id(self, confronto_id: int) -> Confronto | None:
        raise NotImplementedError

    @abstractmethod
    def proximo_id(self) -> int:
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
