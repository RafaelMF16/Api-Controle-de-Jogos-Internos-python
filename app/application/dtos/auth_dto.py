from pydantic import BaseModel, EmailStr, Field

from app.application.dtos.usuario_dto import UsuarioOutput


class LoginInput(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=6)


class AuthResponse(BaseModel):
    accessToken: str
    tokenType: str = "Bearer"
    user: UsuarioOutput
