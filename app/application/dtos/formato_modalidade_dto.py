from pydantic import BaseModel, Field, model_validator

from app.domain.entities.confronto import StatusConfronto
from app.domain.entities.equipe import ModalidadeEquipe
from app.domain.entities.formato_modalidade import GrupoConfig, PontuacaoConfig, TipoFormato


class FormatoModalidadeInput(BaseModel):
    tipo: TipoFormato
    fases: list[str] = Field(default_factory=list)
    grupos: list[GrupoConfig] = Field(default_factory=list)
    pontuacao: PontuacaoConfig = Field(default_factory=PontuacaoConfig)

    @model_validator(mode="after")
    def validar_consistencia(self):
        if self.tipo == TipoFormato.MATA_MATA and not self.fases:
            raise ValueError("Formato mata-mata requer ao menos uma fase (ex: 'Final').")
        if self.tipo == TipoFormato.GRUPOS_MATA_MATA:
            if not self.grupos:
                raise ValueError("Formato grupos+mata-mata requer ao menos um grupo.")
            if not self.fases:
                raise ValueError("Formato grupos+mata-mata requer ao menos uma fase de mata-mata.")
        return self


class PosicaoClassificacao(BaseModel):
    posicao: int
    equipe: str
    equipeId: int | None = None
    jogos: int
    vitorias: int
    empates: int
    derrotas: int
    golsPro: int
    golsContra: int
    saldoGols: int
    pontos: int


class ClassificacaoGrupo(BaseModel):
    nome: str
    posicoes: list[PosicaoClassificacao]


class BracketConfronto(BaseModel):
    confrontoId: int
    equipeA: str
    equipeB: str
    golsA: int | None = None
    golsB: int | None = None
    vencedor: str | None = None
    status: StatusConfronto


class RankingResponse(BaseModel):
    tipo: TipoFormato
    modalidade: ModalidadeEquipe
    pontuacao: PontuacaoConfig | None = None
    classificacao: list[PosicaoClassificacao] | None = None
    grupos: list[ClassificacaoGrupo] | None = None
    fases: list[str] | None = None
    confrontosPorFase: dict[str, list[BracketConfronto]] | None = None
