from fastapi import HTTPException, status

from app.application.dtos.cursor_pagination_dto import CursorPaginatedResponse
from app.application.dtos.usuario_dto import UsuarioCreateInput, UsuarioUpdateInput, VisitorRegisterInput
from app.core.cache import MemoryCache
from app.core.config import Settings
from app.core.security import hash_password
from app.domain.entities.usuario import RoleUsuario, Usuario
from app.domain.repositories.usuario_repository import UsuarioRepository


class UsuarioService:
    def __init__(self, repository: UsuarioRepository, cache: MemoryCache, settings: Settings) -> None:
        self.repository = repository
        self.cache = cache
        self.settings = settings

    def listar_usuarios_paginado(self, *, limit: int = 10, cursor: str | None = None) -> CursorPaginatedResponse[Usuario]:
        return self.repository.listar_paginado(limit=limit, cursor=cursor)

    def obter_usuario(self, usuario_id: int) -> Usuario | None:
        return self.cache.get_or_set(
            f"usuarios:id:{usuario_id}",
            self.settings.data_cache_ttl_seconds,
            lambda: self.repository.obter_por_id(usuario_id),
        )

    def obter_usuario_por_username(self, username: str) -> Usuario | None:
        username_normalizado = username.strip().lower()
        return self.cache.get_or_set(
            f"usuarios:username:{username_normalizado}",
            self.settings.data_cache_ttl_seconds,
            lambda: self.repository.obter_por_username(username_normalizado),
        )

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
        criado = self.repository.criar(usuario)
        self._invalidar_cache()
        return criado

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
        criado = self.repository.criar(usuario)
        self._invalidar_cache()
        return criado

    def atualizar_usuario(self, usuario_id: int, payload: UsuarioUpdateInput) -> Usuario | None:
        atual = self.repository.obter_por_id(usuario_id)
        if atual is None:
            return None

        existente = self.repository.obter_por_username(payload.username)
        if existente is not None and existente.id != usuario_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ja existe um usuario com este nome de usuario.",
            )

        equipe_id = atual.equipeId if payload.role == RoleUsuario.CAPITAO else None
        curso = payload.curso if payload.role in {RoleUsuario.VISITANTE, RoleUsuario.CAPITAO} else None
        periodo = payload.periodo if payload.role in {RoleUsuario.VISITANTE, RoleUsuario.CAPITAO} else None

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
        resultado = self.repository.atualizar(usuario_id, usuario_atualizado)
        self._invalidar_cache()
        return resultado

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
        resultado = self.repository.atualizar(usuario_id, usuario_atualizado)
        self._invalidar_cache()
        return resultado

    def remover_usuario(self, usuario_id: int) -> bool:
        removeu = self.repository.remover(usuario_id)
        if removeu:
            self._invalidar_cache()
        return removeu

    def ensure_bootstrap_admin(
        self,
        nome: str | None,
        username: str | None,
        senha: str | None,
    ) -> Usuario | None:
        if not nome or not username or not senha:
            return None

        if self.repository.possui_registros():
            return None

        criado = self.repository.criar(
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
        self._invalidar_cache()
        return criado

    def _proximo_id_usuario(self) -> int:
        return self.repository.proximo_id()

    def _garantir_username_disponivel(self, username: str) -> None:
        existente = self.obter_usuario_por_username(username)
        if existente is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ja existe um usuario com este nome de usuario.",
            )

    def _listar_todos_usuarios(self) -> list[Usuario]:
        return self.cache.get_or_set(
            "usuarios:list:all",
            self.settings.data_cache_ttl_seconds,
            self.repository.listar,
        )

    def _invalidar_cache(self) -> None:
        self.cache.invalidate_prefix("usuarios:")
