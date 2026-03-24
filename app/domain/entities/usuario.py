from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class RoleUsuario(str, Enum):
    ADMIN = "admin"
    JUIZ = "juiz"
    CAPITAO = "capitao"
    VISITANTE = "visitante"


class Usuario(BaseModel):
    id: int
    nome: str = Field(min_length=2)
    email: EmailStr
    role: RoleUsuario
    equipeId: int | None = None
    ativo: bool = True
    senhaHash: str = Field(min_length=1)
