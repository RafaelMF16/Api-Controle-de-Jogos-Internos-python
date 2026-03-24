from app.domain.entities.confronto import Confronto
from app.domain.repositories.confronto_repository import ConfrontoRepository
from app.infrastructure.persistence.firestore.firestore_client import FirestoreDatabase


class FirestoreConfrontoRepository(ConfrontoRepository):
    def __init__(self, database: FirestoreDatabase) -> None:
        self.collection = database.confrontos_collection

    def listar(self) -> list[Confronto]:
        documentos = self.collection.order_by("id").stream()
        return [Confronto.model_validate(documento.to_dict()) for documento in documentos]

    def obter_por_id(self, confronto_id: int) -> Confronto | None:
        documento = self.collection.document(str(confronto_id)).get()
        if not documento.exists:
            return None
        return Confronto.model_validate(documento.to_dict())

    def criar(self, confronto: Confronto) -> Confronto:
        self.collection.document(str(confronto.id)).set(confronto.model_dump(mode="json"))
        return confronto

    def atualizar(self, confronto_id: int, confronto: Confronto) -> Confronto | None:
        referencia = self.collection.document(str(confronto_id))
        if not referencia.get().exists:
            return None

        referencia.set(confronto.model_dump(mode="json"))
        return confronto

    def remover(self, confronto_id: int) -> bool:
        referencia = self.collection.document(str(confronto_id))
        if not referencia.get().exists:
            return False

        referencia.delete()
        return True
