from pydantic import BaseModel, Field

from app.domain.entities.confronto import Confronto


class ResumoDashboard(BaseModel):
    totalEquipes: int = Field(ge=0)
    totalConfrontos: int = Field(ge=0)
    confrontosEncerrados: int = Field(ge=0)
    proximosConfrontos: list[Confronto] = Field(default_factory=list)
