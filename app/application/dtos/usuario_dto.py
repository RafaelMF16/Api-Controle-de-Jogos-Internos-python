from pydantic import BaseModel, EmailStr, Field, model_validator

from app.domain.entities.usuario import RoleUsuario, Usuario


class UsuarioBaseInput(BaseModel):
    nome: str = Field(min_length=2)
    email: EmailStr
    role: RoleUsuario
    equipeId: int | None = None
    ativo: bool = True

    @model_validator(mode="after")
    def validar_capitao(self) -> "UsuarioBaseInput":
        if self.role == RoleUsuario.CAPITAO and self.equipeId is None:
            raise ValueError("Capitão precisa estar vinculado a uma equipe.")

        if self.role != RoleUsuario.CAPITAO:
            self.equipeId = None

        return self


class UsuarioCreateInput(UsuarioBaseInput):
    senha: str = Field(min_length=6)


class UsuarioUpdateInput(UsuarioBaseInput):
    senha: str | None = Field(default=None, min_length=6)


class UsuarioOutput(BaseModel):
    id: int
    nome: str
    email: EmailStr
    role: RoleUsuario
    equipeId: int | None = None
    ativo: bool = True

    @classmethod
    def from_entity(cls, usuario: Usuario) -> "UsuarioOutput":
        return cls(
            id=usuario.id,
            nome=usuario.nome,
            email=usuario.email,
            role=usuario.role,
            equipeId=usuario.equipeId,
            ativo=usuario.ativo,
        )
