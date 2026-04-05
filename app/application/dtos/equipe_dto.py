from pydantic import BaseModel, Field, model_validator

from app.domain.entities.equipe import ModalidadeEquipe


class MembroInput(BaseModel):
    id: int | None = None
    nome: str = Field(min_length=2)
    habilidades: list[str] = Field(default_factory=list)
    funcao: str | None = None


class EquipeInput(BaseModel):
    nome: str = Field(min_length=2)
    responsavel: str | None = None
    curso: str | None = None
    periodo: str | None = None
    modalidade: ModalidadeEquipe
    membros: list[MembroInput] = Field(default_factory=list)
    usuarioId: int | None = None
    icone: str | None = None
    nivelTecnico: int | None = Field(default=None, ge=1, le=5)
    nivelEquipe: int | None = Field(default=None, ge=1, le=5)
    experiencia: str | None = None

    @model_validator(mode="after")
    def validar_por_categoria(self):
        if self.modalidade == ModalidadeEquipe.NATACAO:
            self.responsavel = None
            self.membros = []
            self.nivelEquipe = None
            if self.nivelTecnico is None:
                raise ValueError("Esportes individuais exigem nivel tecnico.")
            return self

        if not self.curso or not self.periodo:
            raise ValueError("Esportes coletivos exigem curso e periodo.")

        self.nivelTecnico = None
        self.experiencia = None
        return self
