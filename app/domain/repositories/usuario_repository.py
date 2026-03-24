from abc import ABC, abstractmethod

from app.domain.entities.usuario import Usuario


class UsuarioRepository(ABC):
    @abstractmethod
    def listar(self) -> list[Usuario]:
        raise NotImplementedError

    @abstractmethod
    def obter_por_id(self, usuario_id: int) -> Usuario | None:
        raise NotImplementedError

    @abstractmethod
    def obter_por_email(self, email: str) -> Usuario | None:
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
