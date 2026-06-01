from abc import ABC, abstractmethod

from app.domain.entities.equipe import ModalidadeEquipe
from app.domain.entities.formato_modalidade import FormatoModalidade


class FormatoModalidadeRepository(ABC):
    @abstractmethod
    def listar(self) -> list[FormatoModalidade]:
        raise NotImplementedError

    @abstractmethod
    def obter(self, modalidade: ModalidadeEquipe) -> FormatoModalidade | None:
        raise NotImplementedError

    @abstractmethod
    def salvar(self, formato: FormatoModalidade) -> FormatoModalidade:
        raise NotImplementedError

    @abstractmethod
    def remover(self, modalidade: ModalidadeEquipe) -> bool:
        raise NotImplementedError
