from app.domain.entities.equipe import Equipe
from app.domain.repositories.equipe_repository import EquipeRepository
from app.infrastructure.persistence.json_db.json_database import JsonDatabase


class JsonEquipeRepository(EquipeRepository):
    def __init__(self, database: JsonDatabase) -> None:
        self.database = database

    def listar(self) -> list[Equipe]:
        data = self.database.read()
        return [Equipe.model_validate(item) for item in data["equipes"]]

    def obter_por_id(self, equipe_id: int) -> Equipe | None:
        return next((equipe for equipe in self.listar() if equipe.id == equipe_id), None)

    def criar(self, equipe: Equipe) -> Equipe:
        data = self.database.read()
        data["equipes"].append(equipe.model_dump())
        self.database.write(data)
        return equipe

    def atualizar(self, equipe_id: int, equipe: Equipe) -> Equipe | None:
        data = self.database.read()
        indice = next((i for i, item in enumerate(data["equipes"]) if item["id"] == equipe_id), None)
        if indice is None:
            return None

        data["equipes"][indice] = equipe.model_dump()
        self.database.write(data)
        return equipe

    def remover(self, equipe_id: int) -> bool:
        data = self.database.read()
        total_original = len(data["equipes"])
        data["equipes"] = [item for item in data["equipes"] if item["id"] != equipe_id]
        removeu = len(data["equipes"]) != total_original
        if removeu:
            self.database.write(data)
        return removeu
