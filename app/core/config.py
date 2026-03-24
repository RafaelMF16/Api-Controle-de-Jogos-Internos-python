import os
from dataclasses import dataclass
from functools import lru_cache
import json


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    api_prefix: str
    google_cloud_project: str | None
    firestore_equipes_collection: str
    firestore_confrontos_collection: str
    firestore_usuarios_collection: str
    allowed_origins: list[str]
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    bootstrap_admin_name: str | None
    bootstrap_admin_email: str | None
    bootstrap_admin_password: str | None


def _parse_allowed_origins(raw_value: str | None) -> list[str]:
    if not raw_value:
        return ["http://localhost:4200"]

    try:
        parsed = json.loads(raw_value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except json.JSONDecodeError:
        pass

    return [item.strip() for item in raw_value.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Jogos Internos API"),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        api_prefix=os.getenv("API_PREFIX", "/api/v1"),
        google_cloud_project=os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT"),
        firestore_equipes_collection=os.getenv("FIRESTORE_EQUIPES_COLLECTION", "equipes"),
        firestore_confrontos_collection=os.getenv("FIRESTORE_CONFRONTOS_COLLECTION", "confrontos"),
        firestore_usuarios_collection=os.getenv("FIRESTORE_USUARIOS_COLLECTION", "usuarios"),
        allowed_origins=_parse_allowed_origins(os.getenv("ALLOWED_ORIGINS")),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", "troque-esta-chave-em-producao"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480")),
        bootstrap_admin_name=os.getenv("BOOTSTRAP_ADMIN_NAME"),
        bootstrap_admin_email=os.getenv("BOOTSTRAP_ADMIN_EMAIL"),
        bootstrap_admin_password=os.getenv("BOOTSTRAP_ADMIN_PASSWORD"),
    )
