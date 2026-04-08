from enum import Enum

from pydantic import BaseModel, Field, model_validator


class ModalidadeEquipe(str, Enum):
    FUTSAL = "Futsal"
    VOLEI = "Volei"
    QUEIMADA = "Queimada"
    BASQUETE = "Basquete"
    NATACAO = "Natacao"


class Membro(BaseModel):
    id: int
    nome: str = Field(min_length=2)
    habilidades: list[str] = Field(default_factory=list)
    funcao: str | None = None


class Equipe(BaseModel):
    id: int
    nome: str = Field(min_length=2)
    responsavel: str | None = None
    curso: str = Field(min_length=2)
    periodo: str = Field(min_length=1)
    modalidade: ModalidadeEquipe
    membros: list[Membro] = Field(default_factory=list)
    usuarioId: int | None = None
    icone: str | None = None

    @model_validator(mode="after")
    def validar_por_categoria(self):
        if self.modalidade == ModalidadeEquipe.NATACAO:
            self.responsavel = None
            self.membros = []
            return self

        self.usuarioId = None
        if not self.responsavel or len(self.responsavel.strip()) < 2:
            raise ValueError("Esportes coletivos exigem um responsável válido.")
        return self
