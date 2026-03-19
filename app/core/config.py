import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    api_prefix: str
    database_file: Path
    allowed_origins: list[str]


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
    project_root = Path(__file__).resolve().parents[2]

    return Settings(
        app_name=os.getenv("APP_NAME", "Jogos Internos API"),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        api_prefix=os.getenv("API_PREFIX", "/api/v1"),
        database_file=project_root / "data" / "database.json",
        allowed_origins=_parse_allowed_origins(os.getenv("ALLOWED_ORIGINS")),
    )
