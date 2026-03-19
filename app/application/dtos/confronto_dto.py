from pydantic import BaseModel, Field

from app.domain.entities.confronto import StatusConfronto


class ConfrontoInput(BaseModel):
    equipeA: str = Field(min_length=2)
    equipeB: str = Field(min_length=2)
    data: str
    horario: str
    local: str = Field(min_length=2)
    golsA: int | None = None
    golsB: int | None = None
    modalidade: str | None = None
    status: StatusConfronto | None = StatusConfronto.AGENDADO
    destaque: bool | None = None
    periodoAtual: str | None = None
    duracao: str | None = None
    fase: str | None = None
