from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.domain.entities.equipe import ModalidadeEquipe


class StatusConfronto(str, Enum):
    AGENDADO = "agendado"
    AO_VIVO = "ao-vivo"
    ENCERRADO = "encerrado"


class StatusPrevisao(str, Enum):
    PENDENTE = "pending"
    PRONTA = "ready"
    ERRO = "error"


class PrevisaoConfronto(BaseModel):
    status: StatusPrevisao = StatusPrevisao.PENDENTE
    chanceA: int | None = None
    chanceB: int | None = None
    favorito: str | None = None
    resumo: str | None = None
    modelo: str | None = None
    geradaEm: str | None = None
    precisaRegerar: bool = False
    erro: str | None = None

    @classmethod
    def pendente(cls) -> "PrevisaoConfronto":
        return cls(status=StatusPrevisao.PENDENTE)

    @classmethod
    def erro_previsao(cls, mensagem: str, modelo: str | None = None) -> "PrevisaoConfronto":
        return cls(
            status=StatusPrevisao.ERRO,
            resumo="Nao foi possivel gerar a previsao automaticamente.",
            modelo=modelo,
            geradaEm=datetime.now(UTC).isoformat(),
            erro=mensagem,
        )


class Confronto(BaseModel):
    id: int
    equipeA: str = Field(min_length=2)
    equipeB: str = Field(min_length=2)
    participanteAId: int | None = None
    participanteBId: int | None = None
    data: str
    horario: str
    local: str = Field(min_length=2)
    golsA: int | None = None
    golsB: int | None = None
    vencedor: str | None = None
    modalidade: ModalidadeEquipe
    status: StatusConfronto = StatusConfronto.AGENDADO
    destaque: bool | None = None
    periodoAtual: str | None = None
    duracao: str | None = None
    fase: str | None = None
    previsao: PrevisaoConfronto = Field(default_factory=PrevisaoConfronto.pendente)
