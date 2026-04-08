from google.cloud.firestore_v1 import FieldFilter, Query

from app.application.dtos.cursor_pagination_dto import CursorPaginatedResponse
from app.domain.entities.equipe import Equipe
from app.domain.entities.equipe import ModalidadeEquipe
from app.domain.repositories.equipe_repository import EquipeRepository
from app.infrastructure.persistence.firestore.firestore_client import FirestoreDatabase


class FirestoreEquipeRepository(EquipeRepository):
    def __init__(self, database: FirestoreDatabase) -> None:
        self.database = database
        self.collection = database.equipes_collection

    def listar(self) -> list[Equipe]:
        documentos = self.collection.order_by("id").stream()
        return [Equipe.model_validate(documento.to_dict()) for documento in documentos]

    def listar_paginado(
        self,
        *,
        categoria: str | None,
        limit: int,
        cursor: str | None,
    ) -> CursorPaginatedResponse[Equipe]:
        query = self.collection.order_by("id", direction=Query.DESCENDING)

        if cursor:
            query = query.start_after({"id": int(cursor)})

        documentos = query.stream()
        itens: list[Equipe] = []
        ultimo_id: int | None = None
        lidos = 0
        limite_leitura = max(limit * 6, 30)

        for documento in documentos:
            dados = documento.to_dict() or {}
            ultimo_id = int(dados.get("id", 0))
            lidos += 1

            equipe = Equipe.model_validate(dados)
            if self._categoria_confere(equipe, categoria):
                itens.append(equipe)
                if len(itens) == limit + 1:
                    break

            if lidos >= limite_leitura and len(itens) >= limit:
                break

        has_next = len(itens) > limit
        itens_pagina = itens[:limit]
        next_cursor = str(itens_pagina[-1].id) if has_next and itens_pagina else None

        return CursorPaginatedResponse(
            items=itens_pagina,
            page_size=limit,
            next_cursor=next_cursor,
            has_next=has_next,
        )

    def obter_por_id(self, equipe_id: int) -> Equipe | None:
        documento = self.collection.document(str(equipe_id)).get()
        if not documento.exists:
            return None
        return Equipe.model_validate(documento.to_dict())

    def obter_por_nome_modalidade(self, nome: str, modalidade: str) -> Equipe | None:
        documentos = self.collection.where(
            filter=FieldFilter("nome", "==", nome)
        ).where(
            filter=FieldFilter("modalidade", "==", modalidade)
        ).limit(1).stream()
        for documento in documentos:
            return Equipe.model_validate(documento.to_dict())
        return None

    def obter_inscricao_individual(self, usuario_id: int, modalidade: str) -> Equipe | None:
        documentos = self.collection.where(
            filter=FieldFilter("usuarioId", "==", usuario_id)
        ).where(
            filter=FieldFilter("modalidade", "==", modalidade)
        ).limit(1).stream()
        for documento in documentos:
            return Equipe.model_validate(documento.to_dict())
        return None

    def proximo_id(self) -> int:
        return self.database.next_sequence("equipes", seed=self._ultimo_id())

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

    def _ultimo_id(self) -> int:
        documentos = self.collection.order_by("id", direction=Query.DESCENDING).limit(1).stream()
        for documento in documentos:
            dados = documento.to_dict() or {}
            return int(dados.get("id", 0))
        return 0

    @staticmethod
    def _categoria_confere(equipe: Equipe, categoria: str | None) -> bool:
        if categoria == "individual":
            return equipe.modalidade == ModalidadeEquipe.NATACAO

        if categoria == "coletivo":
            return equipe.modalidade != ModalidadeEquipe.NATACAO

        return True
