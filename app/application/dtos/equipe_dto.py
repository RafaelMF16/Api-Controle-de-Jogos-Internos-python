from pydantic import BaseModel, Field, model_validator

from app.domain.entities.equipe import MAX_HABILIDADES_POR_MEMBRO, ModalidadeEquipe


class MembroInput(BaseModel):
    id: int | None = None
    nome: str = Field(min_length=2)
    habilidades: list[str] = Field(default_factory=list, max_length=MAX_HABILIDADES_POR_MEMBRO)
    funcao: str | None = None
    usuarioId: int | None = None

    @model_validator(mode="after")
    def validar_habilidades(self):
        self.habilidades = [habilidade.strip() for habilidade in self.habilidades if habilidade and habilidade.strip()]
        if len(self.habilidades) > MAX_HABILIDADES_POR_MEMBRO:
            raise ValueError(f"Cada membro pode ter no maximo {MAX_HABILIDADES_POR_MEMBRO} habilidades.")
        return self


class EquipeInput(BaseModel):
    nome: str = Field(min_length=2)
    responsavel: str | None = None
    curso: str | None = None
    periodo: str | None = None
    modalidade: ModalidadeEquipe
    membros: list[MembroInput] = Field(default_factory=list)
    usuarioId: int | None = None
    icone: str | None = None

    @model_validator(mode="after")
    def validar_por_categoria(self):
        if self.modalidade == ModalidadeEquipe.NATACAO:
            self.responsavel = None
            self.membros = []
            return self

        if not self.curso or not self.periodo:
            raise ValueError("Esportes coletivos exigem curso e periodo.")

        return self
