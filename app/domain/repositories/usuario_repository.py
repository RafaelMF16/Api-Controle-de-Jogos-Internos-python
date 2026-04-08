from abc import ABC, abstractmethod

from app.application.dtos.cursor_pagination_dto import CursorPaginatedResponse
from app.domain.entities.usuario import Usuario


class UsuarioRepository(ABC):
    @abstractmethod
    def listar(self) -> list[Usuario]:
        raise NotImplementedError

    @abstractmethod
    def listar_paginado(self, *, limit: int, cursor: str | None) -> CursorPaginatedResponse[Usuario]:
        raise NotImplementedError

    @abstractmethod
    def obter_por_id(self, usuario_id: int) -> Usuario | None:
        raise NotImplementedError

    @abstractmethod
    def obter_por_username(self, username: str) -> Usuario | None:
        raise NotImplementedError

    @abstractmethod
    def possui_registros(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def proximo_id(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def criar(self, usuario: Usuario) -> Usuario:
        raise NotImplementedError

    @abstractmethod
    def atualizar(self, usuario_id: int, usuario: Usuario) -> Usuario | None:
        raise NotImplementedError

    @abstractmethod
    def remover(self, usuario_id: int) -> bool:
        raise NotImplementedError
