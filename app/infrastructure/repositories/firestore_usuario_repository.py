from google.cloud.firestore_v1 import FieldFilter, Query

from app.application.dtos.cursor_pagination_dto import CursorPaginatedResponse
from app.domain.entities.usuario import Usuario
from app.domain.repositories.usuario_repository import UsuarioRepository
from app.infrastructure.persistence.firestore.firestore_client import FirestoreDatabase


class FirestoreUsuarioRepository(UsuarioRepository):
    def __init__(self, database: FirestoreDatabase) -> None:
        self.database = database
        self.collection = database.usuarios_collection

    def listar(self) -> list[Usuario]:
        documentos = self.collection.order_by("id").stream()
        return [self._to_usuario(documento.to_dict()) for documento in documentos]

    def listar_paginado(self, *, limit: int, cursor: str | None) -> CursorPaginatedResponse[Usuario]:
        query = self.collection.order_by("id", direction=Query.DESCENDING).limit(limit + 1)

        if cursor:
            query = query.start_after({"id": int(cursor)})

        documentos = list(query.stream())
        has_next = len(documentos) > limit
        documentos_pagina = documentos[:limit]
        items = [self._to_usuario(documento.to_dict()) for documento in documentos_pagina]
        next_cursor = str(items[-1].id) if has_next and items else None

        return CursorPaginatedResponse(
            items=items,
            page_size=limit,
            next_cursor=next_cursor,
            has_next=has_next,
        )

    def obter_por_id(self, usuario_id: int) -> Usuario | None:
        documento = self.collection.document(str(usuario_id)).get()
        if not documento.exists:
            return None
        return self._to_usuario(documento.to_dict())

    def obter_por_username(self, username: str) -> Usuario | None:
        username_normalizado = self._normalize_username(username)
        documentos = self.collection.where(filter=FieldFilter("username", "==", username_normalizado)).limit(1).stream()
        for documento in documentos:
            return self._to_usuario(documento.to_dict())
        return None

    def possui_registros(self) -> bool:
        documentos = self.collection.limit(1).stream()
        for _ in documentos:
            return True
        return False

    def proximo_id(self) -> int:
        return self.database.next_sequence("usuarios", seed=self._ultimo_id())

    def criar(self, usuario: Usuario) -> Usuario:
        self.collection.document(str(usuario.id)).set(usuario.model_dump(mode="json"))
        return usuario

    def atualizar(self, usuario_id: int, usuario: Usuario) -> Usuario | None:
        referencia = self.collection.document(str(usuario_id))
        if not referencia.get().exists:
            return None

        referencia.set(usuario.model_dump(mode="json"))
        return usuario

    def desvincular_equipe(self, equipe_id: int) -> int:
        documentos = self.collection.where(filter=FieldFilter("equipeId", "==", equipe_id)).stream()
        total = 0

        for documento in documentos:
            dados = documento.to_dict() or {}
            usuario = self._to_usuario(dados).model_copy(update={"equipeId": None})
            self.collection.document(str(usuario.id)).set(usuario.model_dump(mode="json"))
            total += 1

        return total

    def remover(self, usuario_id: int) -> bool:
        referencia = self.collection.document(str(usuario_id))
        if not referencia.get().exists:
            return False

        referencia.delete()
        return True

    def _to_usuario(self, payload: dict | None) -> Usuario:
        dados = dict(payload or {})
        username = dados.get("username")

        if not username and dados.get("email"):
            username = str(dados["email"]).strip().lower()

        dados["username"] = self._normalize_username(username or "")
        dados.pop("email", None)
        return Usuario.model_validate(dados)

    @staticmethod
    def _normalize_username(username: str) -> str:
        return username.strip().lower()

    def _ultimo_id(self) -> int:
        documentos = self.collection.order_by("id", direction=Query.DESCENDING).limit(1).stream()
        for documento in documentos:
            dados = documento.to_dict() or {}
            return int(dados.get("id", 0))
        return 0
