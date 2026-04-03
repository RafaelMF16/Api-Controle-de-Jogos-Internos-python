from fastapi import HTTPException, status
from jwt import InvalidTokenError

from app.core.cache import MemoryCache
from app.core.config import Settings
from app.core.security import create_access_token, decode_access_token, verify_password
from app.domain.entities.usuario import Usuario
from app.domain.repositories.usuario_repository import UsuarioRepository


class AuthService:
    def __init__(self, repository: UsuarioRepository, settings: Settings, cache: MemoryCache) -> None:
        self.repository = repository
        self.settings = settings
        self.cache = cache

    def autenticar(self, username: str, senha: str) -> tuple[str, Usuario]:
        username_normalizado = username.strip().lower()
        usuario = self._obter_usuario_por_username(username_normalizado)
        if usuario is None or not verify_password(senha, usuario.senhaHash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais invalidas.",
            )

        if not usuario.ativo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inativo.",
            )

        token = create_access_token(
            {
                "sub": str(usuario.id),
                "role": usuario.role.value,
                "equipe_id": usuario.equipeId,
            },
            secret_key=self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
            expires_minutes=self.settings.access_token_expire_minutes,
        )
        return token, usuario

    def obter_usuario_atual(self, token: str) -> Usuario:
        try:
            payload = decode_access_token(
                token,
                secret_key=self.settings.jwt_secret_key,
                algorithm=self.settings.jwt_algorithm,
            )
        except InvalidTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalido ou expirado.",
            ) from exc

        subject = payload.get("sub")
        if subject is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalido.",
            )

        usuario = self._obter_usuario_por_id(int(subject))
        if usuario is None or not usuario.ativo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario nao autorizado.",
            )

        return usuario

    def _obter_usuario_por_id(self, usuario_id: int) -> Usuario | None:
        return self.cache.get_or_set(
            f"usuarios:id:{usuario_id}",
            self.settings.data_cache_ttl_seconds,
            lambda: self.repository.obter_por_id(usuario_id),
        )

    def _obter_usuario_por_username(self, username: str) -> Usuario | None:
        return self.cache.get_or_set(
            f"usuarios:username:{username}",
            self.settings.data_cache_ttl_seconds,
            lambda: self.repository.obter_por_username(username),
        )
