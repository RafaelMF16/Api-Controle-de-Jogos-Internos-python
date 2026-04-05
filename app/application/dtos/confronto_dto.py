from pydantic import BaseModel, Field

from app.domain.entities.confronto import StatusConfronto
from app.domain.entities.equipe import ModalidadeEquipe


class ConfrontoInput(BaseModel):
    equipeA: str = Field(min_length=2)
    equipeB: str = Field(min_length=2)
    participanteAId: int | None = Field(default=None, ge=1)
    participanteBId: int | None = Field(default=None, ge=1)
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
