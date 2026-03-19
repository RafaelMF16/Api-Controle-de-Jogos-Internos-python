from app.domain.entities.confronto import Confronto
from app.domain.repositories.confronto_repository import ConfrontoRepository
from app.infrastructure.persistence.json_db.json_database import JsonDatabase


class JsonConfrontoRepository(ConfrontoRepository):
    def __init__(self, database: JsonDatabase) -> None:
        self.database = database

    def listar(self) -> list[Confronto]:
        data = self.database.read()
        return [Confronto.model_validate(item) for item in data["confrontos"]]

    def obter_por_id(self, confronto_id: int) -> Confronto | None:
        return next((confronto for confronto in self.listar() if confronto.id == confronto_id), None)

    def criar(self, confronto: Confronto) -> Confronto:
        data = self.database.read()
        data["confrontos"].append(confronto.model_dump())
        self.database.write(data)
        return confronto

    def atualizar(self, confronto_id: int, confronto: Confronto) -> Confronto | None:
        data = self.database.read()
        indice = next((i for i, item in enumerate(data["confrontos"]) if item["id"] == confronto_id), None)
        if indice is None:
            return None

        data["confrontos"][indice] = confronto.model_dump()
        self.database.write(data)
        return confronto

    def remover(self, confronto_id: int) -> bool:
        data = self.database.read()
        total_original = len(data["confrontos"])
        data["confrontos"] = [item for item in data["confrontos"] if item["id"] != confronto_id]
        removeu = len(data["confrontos"]) != total_original
        if removeu:
            self.database.write(data)
        return removeu
