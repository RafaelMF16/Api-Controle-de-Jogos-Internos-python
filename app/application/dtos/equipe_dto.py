from pydantic import BaseModel, EmailStr, Field


class MembroInput(BaseModel):
    id: int | None = None
    nome: str = Field(min_length=2)
    habilidades: list[str] = Field(default_factory=list)
    funcao: str | None = None


class EquipeInput(BaseModel):
    nome: str = Field(min_length=2)
    responsavel: str = Field(min_length=2)
    email: EmailStr
    membros: list[MembroInput] = Field(default_factory=list)
    icone: str | None = None
    cor: str | None = None
    sigla: str | None = Field(default=None, min_length=2, max_length=5)
