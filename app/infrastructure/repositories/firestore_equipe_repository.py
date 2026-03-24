from app.domain.entities.equipe import Equipe
from app.domain.repositories.equipe_repository import EquipeRepository
from app.infrastructure.persistence.firestore.firestore_client import FirestoreDatabase


class FirestoreEquipeRepository(EquipeRepository):
    def __init__(self, database: FirestoreDatabase) -> None:
        self.collection = database.equipes_collection

    def listar(self) -> list[Equipe]:
        documentos = self.collection.order_by("id").stream()
        return [Equipe.model_validate(documento.to_dict()) for documento in documentos]

    def obter_por_id(self, equipe_id: int) -> Equipe | None:
        documento = self.collection.document(str(equipe_id)).get()
        if not documento.exists:
            return None
        return Equipe.model_validate(documento.to_dict())

    def criar(self, equipe: Equipe) -> Equipe:
        self.collection.document(str(equipe.id)).set(equipe.model_dump(mode="json"))
        return equipe

    def atualizar(self, equipe_id: int, equipe: Equipe) -> Equipe | None:
        referencia = self.collection.document(str(equipe_id))
        if not referencia.get().exists:
            return None

        referencia.set(equipe.model_dump(mode="json"))
        return equipe

    def remover(self, equipe_id: int) -> bool:
        referencia = self.collection.document(str(equipe_id))
        if not referencia.get().exists:
            return False

        referencia.delete()
        return True
