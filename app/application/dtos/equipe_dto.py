from pydantic import BaseModel, EmailStr, Field

from app.domain.entities.equipe import ModalidadeEquipe


class MembroInput(BaseModel):
    id: int | None = None
    nome: str = Field(min_length=2)
    habilidades: list[str] = Field(default_factory=list)
    funcao: str | None = None


class EquipeInput(BaseModel):
    nome: str = Field(min_length=2)
    responsavel: str = Field(min_length=2)
    email: EmailStr
    modalidade: ModalidadeEquipe
    membros: list[MembroInput] = Field(default_factory=list)
    icone: str | None = None
