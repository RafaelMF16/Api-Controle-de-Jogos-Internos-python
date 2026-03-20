from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class ModalidadeEquipe(str, Enum):
    FUTSAL = "Futsal"
    VOLEI = "Volei"
    BASQUETE = "Basquete"
    NATACAO = "Natacao"
    ATLETISMO = "Atletismo"


class Membro(BaseModel):
    id: int
    nome: str = Field(min_length=2)
    habilidades: list[str] = Field(default_factory=list)
    funcao: str | None = None


class Equipe(BaseModel):
    id: int
    nome: str = Field(min_length=2)
    responsavel: str = Field(min_length=2)
    email: EmailStr
    modalidade: ModalidadeEquipe
    membros: list[Membro] = Field(default_factory=list)
    icone: str | None = None
