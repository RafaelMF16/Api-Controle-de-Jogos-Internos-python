from enum import Enum

from pydantic import BaseModel, Field

from app.domain.entities.equipe import ModalidadeEquipe


class TipoFormato(str, Enum):
    LIGA = "liga"
    MATA_MATA = "mata-mata"
    GRUPOS_MATA_MATA = "grupos+mata-mata"


class PontuacaoConfig(BaseModel):
    vitoria: int = Field(default=3, ge=0, le=10)
    empate: int = Field(default=1, ge=0, le=10)
    derrota: int = Field(default=0, ge=0, le=10)


class GrupoConfig(BaseModel):
    nome: str = Field(min_length=1)
    equipes: list[str] = Field(default_factory=list)


class FormatoModalidade(BaseModel):
    modalidade: ModalidadeEquipe
    tipo: TipoFormato
    fases: list[str] = Field(default_factory=list)
    grupos: list[GrupoConfig] = Field(default_factory=list)
    pontuacao: PontuacaoConfig = Field(default_factory=PontuacaoConfig)
