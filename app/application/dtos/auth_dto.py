from pydantic import BaseModel, Field

from app.application.dtos.usuario_dto import UsuarioOutput


class LoginInput(BaseModel):
    username: str = Field(min_length=3)
    senha: str = Field(min_length=6)


class AuthResponse(BaseModel):
    accessToken: str
    tokenType: str = "Bearer"
    user: UsuarioOutput
