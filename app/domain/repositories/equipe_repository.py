from abc import ABC, abstractmethod

from app.application.dtos.cursor_pagination_dto import CursorPaginatedResponse
from app.domain.entities.equipe import Equipe


class EquipeRepository(ABC):
    @abstractmethod
    def listar(self) -> list[Equipe]:
        raise NotImplementedError

    @abstractmethod
    def listar_paginado(
        self,
        *,
        categoria: str | None,
        modalidade: str | None,
        nome_exato: str | None,
        usuario_id: int | None,
        limit: int,
        cursor: str | None,
    ) -> CursorPaginatedResponse[Equipe]:
        raise NotImplementedError

    @abstractmethod
    def contar(
        self,
        *,
        categoria: str | None = None,
        modalidade: str | None = None,
        nome_exato: str | None = None,
        usuario_id: int | None = None,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    def obter_por_id(self, equipe_id: int) -> Equipe | None:
        raise NotImplementedError

    @abstractmethod
    def obter_por_ids(self, equipe_ids: list[int]) -> list[Equipe]:
        raise NotImplementedError

    @abstractmethod
    def obter_por_nome_modalidade(self, nome: str, modalidade: str) -> Equipe | None:
        raise NotImplementedError

    @abstractmethod
    def obter_inscricao_individual(self, usuario_id: int, modalidade: str) -> Equipe | None:
        raise NotImplementedError

    @abstractmethod
    def existe_vinculo_usuario(self, usuario_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def proximo_id(self) -> int:
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
