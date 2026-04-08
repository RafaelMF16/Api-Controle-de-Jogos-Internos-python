from pydantic import BaseModel, Field

from app.application.dtos.usuario_dto import UsuarioOutput, VisitorRegisterInput


class LoginInput(BaseModel):
    username: str = Field(min_length=3)
    senha: str = Field(min_length=6)


class VisitorSignupInput(VisitorRegisterInput):
    pass


class AuthResponse(BaseModel):
    user: UsuarioOutput
