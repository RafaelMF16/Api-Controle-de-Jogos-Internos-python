from fastapi import HTTPException, status

from app.application.dtos.usuario_dto import UsuarioCreateInput, UsuarioUpdateInput, VisitorRegisterInput
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

    def obter_usuario_por_username(self, username: str) -> Usuario | None:
        return self.repository.obter_por_username(username)

    def criar_usuario(self, payload: UsuarioCreateInput) -> Usuario:
        self._garantir_username_disponivel(payload.username)

        usuario = Usuario(
            id=self._proximo_id_usuario(),
            nome=payload.nome,
            username=payload.username,
            role=payload.role,
            equipeId=None,
            curso=payload.curso,
            periodo=payload.periodo,
            ativo=payload.ativo,
            senhaHash=hash_password(payload.senha),
        )
        return self.repository.criar(usuario)

    def registrar_visitante(self, payload: VisitorRegisterInput) -> Usuario:
        self._garantir_username_disponivel(payload.username)

        usuario = Usuario(
            id=self._proximo_id_usuario(),
            nome=payload.nome,
            username=payload.username,
            role=RoleUsuario.VISITANTE,
            equipeId=None,
            curso=payload.curso,
            periodo=payload.periodo,
            ativo=True,
            senhaHash=hash_password(payload.senha),
        )
        return self.repository.criar(usuario)

    def atualizar_usuario(self, usuario_id: int, payload: UsuarioUpdateInput) -> Usuario | None:
        atual = self.repository.obter_por_id(usuario_id)
        if atual is None:
            return None

        existente = self.repository.obter_por_username(payload.username)
        if existente is not None and existente.id != usuario_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um usuário com este nome de usuário.",
            )

        equipe_id = atual.equipeId if payload.role == RoleUsuario.CAPITAO else None
        curso = payload.curso if payload.role == RoleUsuario.VISITANTE else None
        periodo = payload.periodo if payload.role == RoleUsuario.VISITANTE else None

        usuario_atualizado = Usuario(
            id=usuario_id,
            nome=payload.nome,
            username=payload.username,
            role=payload.role,
            equipeId=equipe_id,
            curso=curso,
            periodo=periodo,
            ativo=payload.ativo,
            senhaHash=hash_password(payload.senha) if payload.senha else atual.senhaHash,
        )
        return self.repository.atualizar(usuario_id, usuario_atualizado)

    def vincular_equipe(self, usuario_id: int, equipe_id: int) -> Usuario | None:
        atual = self.repository.obter_por_id(usuario_id)
        if atual is None:
            return None

        usuario_atualizado = Usuario(
            id=atual.id,
            nome=atual.nome,
            username=atual.username,
            role=atual.role,
            equipeId=equipe_id,
            curso=atual.curso,
            periodo=atual.periodo,
            ativo=atual.ativo,
            senhaHash=atual.senhaHash,
        )
        return self.repository.atualizar(usuario_id, usuario_atualizado)

    def remover_usuario(self, usuario_id: int) -> bool:
        return self.repository.remover(usuario_id)

    def ensure_bootstrap_admin(
        self,
        nome: str | None,
        username: str | None,
        senha: str | None,
    ) -> Usuario | None:
        if not nome or not username or not senha:
            return None

        if self.repository.listar():
            return None

        return self.repository.criar(
            Usuario(
                id=1,
                nome=nome,
                username=username.strip().lower(),
                role=RoleUsuario.ADMIN,
                equipeId=None,
                curso=None,
                periodo=None,
                ativo=True,
                senhaHash=hash_password(senha),
            )
        )

    def _proximo_id_usuario(self) -> int:
        usuarios = self.repository.listar()
        return max((usuario.id for usuario in usuarios), default=0) + 1

    def _garantir_username_disponivel(self, username: str) -> None:
        existente = self.repository.obter_por_username(username)
        if existente is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um usuário com este nome de usuário.",
            )
