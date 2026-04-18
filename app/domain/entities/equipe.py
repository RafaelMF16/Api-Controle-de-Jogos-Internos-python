from enum import Enum

from pydantic import BaseModel, Field, model_validator

CAPITAO_FUNCAO = "Capitao"
ATLETA_FUNCAO = "Atleta"
MAX_HABILIDADES_POR_MEMBRO = 3
LIMITES_INTEGRANTES_POR_MODALIDADE: dict[str, int] = {
    "Futsal": 14,
    "Volei": 12,
    "Queimada": 10,
    "TenisDeMesa": 2,
    "TenisDeMesaIndividual": 1,
}


class ModalidadeEquipe(str, Enum):
    FUTSAL = "Futsal"
    VOLEI = "Volei"
    QUEIMADA = "Queimada"
    TENIS_DE_MESA = "TenisDeMesa"
    TENIS_DE_MESA_INDIVIDUAL = "TenisDeMesaIndividual"


MODALIDADES_INDIVIDUAIS: frozenset[ModalidadeEquipe] = frozenset({ModalidadeEquipe.TENIS_DE_MESA_INDIVIDUAL})


class Membro(BaseModel):
    id: int
    nome: str = Field(min_length=2)
    habilidades: list[str] = Field(default_factory=list, max_length=MAX_HABILIDADES_POR_MEMBRO)
    funcao: str | None = None
    nivel: str | None = None
    especialidade: str | None = None
    genero: str | None = None
    usuarioId: int | None = None

    @model_validator(mode="after")
    def validar_habilidades(self):
        self.habilidades = [habilidade.strip() for habilidade in self.habilidades if habilidade and habilidade.strip()]
        if len(self.habilidades) > MAX_HABILIDADES_POR_MEMBRO:
            raise ValueError(f"Cada membro pode ter no maximo {MAX_HABILIDADES_POR_MEMBRO} habilidades.")
        self.nivel = self.nivel.strip() if self.nivel and self.nivel.strip() else None
        self.especialidade = self.especialidade.strip() if self.especialidade and self.especialidade.strip() else None
        if self.genero:
            self.genero = self.genero.strip().upper() or None
        return self


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
        if self.modalidade in MODALIDADES_INDIVIDUAIS:
            self.responsavel = None
            return self

        self.usuarioId = None
        if not self.responsavel or len(self.responsavel.strip()) < 2:
            raise ValueError("Esportes coletivos exigem um responsavel valido.")

        return self


def obter_limite_integrantes(modalidade: ModalidadeEquipe | str) -> int:
    chave = modalidade.value if isinstance(modalidade, ModalidadeEquipe) else str(modalidade)
    return LIMITES_INTEGRANTES_POR_MODALIDADE[chave]


def eh_membro_capitao(membro: Membro) -> bool:
    return (membro.funcao or "").strip().lower() == CAPITAO_FUNCAO.lower()
