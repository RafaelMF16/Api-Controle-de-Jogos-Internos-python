import json
import os
from dataclasses import dataclass
from functools import lru_cache


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
    auth_cookie_name: str
    auth_cookie_secure: bool
    auth_cookie_samesite: str
    data_cache_ttl_seconds: int
    dashboard_cache_ttl_seconds: int
    prediction_provider: str
    prediction_model: str
    vertex_ai_location: str
    prediction_fallback_provider: str
    bootstrap_admin_name: str | None
    bootstrap_admin_username: str | None
    bootstrap_admin_password: str | None


def _parse_allowed_origins(raw_value: str | None) -> list[str]:
    if not raw_value:
        return ["http://localhost:4200", "http://127.0.0.1:4200"]

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
        auth_cookie_name=os.getenv("AUTH_COOKIE_NAME", "ug_access_token"),
        auth_cookie_secure=os.getenv("AUTH_COOKIE_SECURE", "false").strip().lower() == "true",
        auth_cookie_samesite=os.getenv("AUTH_COOKIE_SAMESITE", "lax").strip().lower(),
        data_cache_ttl_seconds=int(os.getenv("DATA_CACHE_TTL_SECONDS", "30")),
        dashboard_cache_ttl_seconds=int(os.getenv("DASHBOARD_CACHE_TTL_SECONDS", "20")),
        prediction_provider=os.getenv("PREDICTION_PROVIDER", "heuristic"),
        prediction_model=os.getenv("PREDICTION_MODEL", "gemini-2.5-flash-lite"),
        vertex_ai_location=os.getenv("VERTEX_AI_LOCATION", "us-central1"),
        prediction_fallback_provider=os.getenv("PREDICTION_FALLBACK_PROVIDER", "heuristic"),
        bootstrap_admin_name=os.getenv("BOOTSTRAP_ADMIN_NAME"),
        bootstrap_admin_username=os.getenv("BOOTSTRAP_ADMIN_USERNAME"),
        bootstrap_admin_password=os.getenv("BOOTSTRAP_ADMIN_PASSWORD"),
    )
