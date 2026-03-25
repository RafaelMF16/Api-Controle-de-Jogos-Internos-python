from fastapi import HTTPException, status

from app.application.dtos.usuario_dto import UsuarioCreateInput, UsuarioUpdateInput
from app.core.security import hash_password
from app.domain.entities.usuario import RoleUsuario, Usuario
from app.domain.repositories.usuario_repository import UsuarioRepository


class UsuarioService:
    def __init__(self, repository: UsuarioRepository) -> None:
        self.repository = repository

    def listar_usuarios(self) -> list[Usuario]:
        return self.repository.listar()

    def obter_usuario(self, usuario_id: int) -> Usuario | None:
        return self.repository.obter_por_id(usuario_id)

    def obter_usuario_por_email(self, email: str) -> Usuario | None:
        return self.repository.obter_por_email(email)

    def criar_usuario(self, payload: UsuarioCreateInput) -> Usuario:
        existente = self.repository.obter_por_email(payload.email)
        if existente is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um usuário com este e-mail.",
            )

        usuario = Usuario(
            id=self._proximo_id_usuario(),
            nome=payload.nome,
            email=payload.email,
            role=payload.role,
            equipeId=payload.equipeId,
            ativo=payload.ativo,
            senhaHash=hash_password(payload.senha),
        )
        return self.repository.criar(usuario)

    def atualizar_usuario(self, usuario_id: int, payload: UsuarioUpdateInput) -> Usuario | None:
        atual = self.repository.obter_por_id(usuario_id)
        if atual is None:
            return None

        existente = self.repository.obter_por_email(payload.email)
        if existente is not None and existente.id != usuario_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um usuário com este e-mail.",
            )

        usuario_atualizado = Usuario(
            id=usuario_id,
            nome=payload.nome,
            email=payload.email,
            role=payload.role,
            equipeId=payload.equipeId,
            ativo=payload.ativo,
            senhaHash=hash_password(payload.senha) if payload.senha else atual.senhaHash,
        )
        return self.repository.atualizar(usuario_id, usuario_atualizado)

    def remover_usuario(self, usuario_id: int) -> bool:
        return self.repository.remover(usuario_id)

    def ensure_bootstrap_admin(
        self,
        nome: str | None,
        email: str | None,
        senha: str | None,
    ) -> Usuario | None:
        if not nome or not email or not senha:
            return None

        if self.repository.listar():
            return None

        return self.repository.criar(
            Usuario(
                id=1,
                nome=nome,
                email=email,
                role=RoleUsuario.ADMIN,
                equipeId=None,
                ativo=True,
                senhaHash=hash_password(senha),
            )
        )

    def _proximo_id_usuario(self) -> int:
        usuarios = self.repository.listar()
        return max((usuario.id for usuario in usuarios), default=0) + 1
