import json
from pathlib import Path


class JsonDatabase:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self._ensure_file_exists()

    def read(self) -> dict:
        with self.file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        data.setdefault("equipes", [])
        data.setdefault("confrontos", [])
        return data

    def write(self, payload: dict) -> None:
        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)

    def _ensure_file_exists(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.write(self._default_payload())

    @staticmethod
    def _default_payload() -> dict:
        return {
            "equipes": [],
            "confrontos": [],
        }
