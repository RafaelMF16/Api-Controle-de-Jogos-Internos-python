from app.domain.entities.usuario import Usuario
from app.domain.repositories.usuario_repository import UsuarioRepository
from app.infrastructure.persistence.firestore.firestore_client import FirestoreDatabase


class FirestoreUsuarioRepository(UsuarioRepository):
    def __init__(self, database: FirestoreDatabase) -> None:
        self.collection = database.usuarios_collection

    def listar(self) -> list[Usuario]:
        documentos = self.collection.order_by("id").stream()
        return [Usuario.model_validate(documento.to_dict()) for documento in documentos]

    def obter_por_id(self, usuario_id: int) -> Usuario | None:
        documento = self.collection.document(str(usuario_id)).get()
        if not documento.exists:
            return None
        return Usuario.model_validate(documento.to_dict())

    def obter_por_email(self, email: str) -> Usuario | None:
        documentos = self.collection.where("email", "==", email).limit(1).stream()
        for documento in documentos:
            return Usuario.model_validate(documento.to_dict())
        return None

    def criar(self, usuario: Usuario) -> Usuario:
        self.collection.document(str(usuario.id)).set(usuario.model_dump(mode="json"))
        return usuario

    def atualizar(self, usuario_id: int, usuario: Usuario) -> Usuario | None:
        referencia = self.collection.document(str(usuario_id))
        if not referencia.get().exists:
            return None

        referencia.set(usuario.model_dump(mode="json"))
        return usuario

    def remover(self, usuario_id: int) -> bool:
        referencia = self.collection.document(str(usuario_id))
        if not referencia.get().exists:
            return False

        referencia.delete()
        return True
