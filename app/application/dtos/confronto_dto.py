from pydantic import BaseModel, Field, model_validator

from app.application.utils.profanity_filter import contem_palavrao
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

    @model_validator(mode="after")
    def validar_conteudo(self):
        if contem_palavrao(self.local):
            raise ValueError("Local do confronto contém conteúdo inapropriado.")
        return self
    golsA: int | None = None
    golsB: int | None = None
    vencedor: str | None = None
    modalidade: ModalidadeEquipe
    status: StatusConfronto = StatusConfronto.AGENDADO
    destaque: bool | None = None
    periodoAtual: str | None = None
    duracao: str | None = None
    fase: str | None = None
