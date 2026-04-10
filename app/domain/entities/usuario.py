from enum import Enum

from pydantic import BaseModel, Field


class RoleUsuario(str, Enum):
    ADMIN = "admin"
    JUIZ = "juiz"
    CAPITAO = "capitao"
    VISITANTE = "visitante"


class TemaUsuario(str, Enum):
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"


class Usuario(BaseModel):
    id: int
    nome: str = Field(min_length=2)
    username: str = Field(min_length=3, pattern=r"^[a-zA-Z0-9._-]+$")
    role: RoleUsuario
    equipeId: int | None = None
    curso: str | None = None
    periodo: str | None = None
    ativo: bool = True
    tema: TemaUsuario = TemaUsuario.DARK
    senhaHash: str = Field(min_length=1)
