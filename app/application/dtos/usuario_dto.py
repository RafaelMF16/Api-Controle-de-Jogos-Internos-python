from pydantic import BaseModel, Field, model_validator

from app.application.utils.profanity_filter import contem_palavrao
from app.domain.entities.usuario import RoleUsuario, TemaUsuario, Usuario


class UsuarioBaseInput(BaseModel):
    nome: str = Field(min_length=2)
    username: str = Field(min_length=3, pattern=r"^[a-zA-Z0-9._-]+$")
    role: RoleUsuario
    equipeId: int | None = None
    curso: str | None = None
    periodo: str | None = None
    ativo: bool = True
    tema: TemaUsuario = TemaUsuario.DARK

    @model_validator(mode="after")
    def normalizar_campos(self) -> "UsuarioBaseInput":
        if contem_palavrao(self.nome) or contem_palavrao(self.username):
            raise ValueError("Nome ou username contém conteúdo inapropriado.")

        if self.role != RoleUsuario.CAPITAO:
            self.equipeId = None

        if self.role not in {RoleUsuario.VISITANTE, RoleUsuario.CAPITAO}:
            self.curso = None
            self.periodo = None

        self.username = self.username.strip().lower()
        return self


class UsuarioCreateInput(UsuarioBaseInput):
    senha: str = Field(min_length=6)


class UsuarioUpdateInput(UsuarioBaseInput):
    senha: str | None = Field(default=None, min_length=6)


class VisitorRegisterInput(BaseModel):
    nome: str = Field(min_length=2)
    username: str = Field(min_length=3, pattern=r"^[a-zA-Z0-9._-]+$")
    senha: str = Field(min_length=6)
    curso: str = Field(min_length=2)
    periodo: str = Field(min_length=1)
    tema: TemaUsuario = TemaUsuario.DARK

    @model_validator(mode="after")
    def normalizar_campos(self) -> "VisitorRegisterInput":
        partes_nome = self.nome.strip().split()
        if len(partes_nome) < 2:
            raise ValueError("Informe nome e sobrenome.")

        if contem_palavrao(self.nome) or contem_palavrao(self.username):
            raise ValueError("Nome ou username contém conteúdo inapropriado.")

        self.username = self.username.strip().lower()
        return self


class UsuarioOutput(BaseModel):
    id: int
    nome: str
    username: str
    role: RoleUsuario
    equipeId: int | None = None
    curso: str | None = None
    periodo: str | None = None
    ativo: bool = True
    tema: TemaUsuario = TemaUsuario.DARK

    @classmethod
    def from_entity(cls, usuario: Usuario) -> "UsuarioOutput":
        return cls(
            id=usuario.id,
            nome=usuario.nome,
            username=usuario.username,
            role=usuario.role,
            equipeId=usuario.equipeId,
            curso=usuario.curso,
            periodo=usuario.periodo,
            ativo=usuario.ativo,
            tema=usuario.tema,
        )


class UsuarioTemaInput(BaseModel):
    tema: TemaUsuario
