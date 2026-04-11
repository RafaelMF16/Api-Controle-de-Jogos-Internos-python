from google.cloud.firestore_v1 import FieldFilter, Query
from google.cloud.firestore_v1.base_query import Or

from app.application.dtos.cursor_pagination_dto import CursorPaginatedResponse
from app.domain.entities.confronto import Confronto, StatusConfronto
from app.domain.repositories.confronto_repository import ConfrontoRepository
from app.infrastructure.persistence.firestore.firestore_client import FirestoreDatabase


class FirestoreConfrontoRepository(ConfrontoRepository):
    def __init__(self, database: FirestoreDatabase) -> None:
        self.database = database
        self.collection = database.confrontos_collection

    def listar(self) -> list[Confronto]:
        documentos = self.collection.order_by("id").stream()
        return [Confronto.model_validate(documento.to_dict()) for documento in documentos]

    def listar_paginado(
        self,
        *,
        equipe: str | None,
        modalidade: str | None,
        status: StatusConfronto | None,
        limit: int,
        cursor: str | None,
    ) -> CursorPaginatedResponse[Confronto]:
        query = self.collection

        if equipe:
            query = query.where(
                filter=Or(
                    [
                        FieldFilter("equipeA", "==", equipe),
                        FieldFilter("equipeB", "==", equipe),
                    ]
                )
            )

        if modalidade:
            query = query.where(filter=FieldFilter("modalidade", "==", modalidade))

        if status:
            query = query.where(filter=FieldFilter("status", "==", status.value))

        query = query.order_by("id", direction=Query.DESCENDING).limit(limit + 1)

        if cursor:
            query = query.start_after({"id": int(cursor)})

        documentos = list(query.stream())
        has_next = len(documentos) > limit
        documentos_pagina = documentos[:limit]
        items = [Confronto.model_validate(documento.to_dict()) for documento in documentos_pagina]
        next_cursor = str(items[-1].id) if has_next and items else None

        return CursorPaginatedResponse(
            items=items,
            page_size=limit,
            next_cursor=next_cursor,
            has_next=has_next,
        )

    def contar(self) -> int:
        return self._count_query(self.collection)

    def listar_proximos(self, limit: int = 5) -> list[Confronto]:
        itens: dict[int, Confronto] = {}

        for status in (StatusConfronto.AO_VIVO, StatusConfronto.AGENDADO):
            documentos = self.collection.where(
                filter=FieldFilter("status", "==", status.value)
            ).limit(limit).stream()
            for documento in documentos:
                confronto = Confronto.model_validate(documento.to_dict())
                itens[confronto.id] = confronto

        return sorted(itens.values(), key=lambda confronto: confronto.id, reverse=True)[:limit]

    def obter_por_id(self, confronto_id: int) -> Confronto | None:
        documento = self.collection.document(str(confronto_id)).get()
        if not documento.exists:
            return None
        return Confronto.model_validate(documento.to_dict())

    def listar_historico_relevante(
        self,
        *,
        modalidade: str,
        participante_ids: list[int],
        nomes_participantes: list[str],
        limit: int = 20,
    ) -> list[Confronto]:
        historico: dict[int, Confronto] = {}

        for participante_id in dict.fromkeys(participante_ids):
            if participante_id <= 0:
                continue

            for campo in ("participanteAId", "participanteBId"):
                documentos = self.collection.where(
                    filter=FieldFilter("modalidade", "==", modalidade)
                ).where(
                    filter=FieldFilter("status", "==", StatusConfronto.ENCERRADO.value)
                ).where(
                    filter=FieldFilter(campo, "==", participante_id)
                ).limit(limit).stream()

                for documento in documentos:
                    confronto = Confronto.model_validate(documento.to_dict())
                    historico[confronto.id] = confronto

        for nome in dict.fromkeys(filter(None, nomes_participantes)):
            for campo in ("equipeA", "equipeB"):
                documentos = self.collection.where(
                    filter=FieldFilter("modalidade", "==", modalidade)
                ).where(
                    filter=FieldFilter("status", "==", StatusConfronto.ENCERRADO.value)
                ).where(
                    filter=FieldFilter(campo, "==", nome)
                ).limit(limit).stream()

                for documento in documentos:
                    confronto = Confronto.model_validate(documento.to_dict())
                    historico[confronto.id] = confronto

        return sorted(historico.values(), key=lambda confronto: confronto.id, reverse=True)[:limit]

    def existe_com_participante(self, participante_id: int, nome: str | None = None) -> bool:
        if self._existe_por_campo("participanteAId", participante_id):
            return True

        if self._existe_por_campo("participanteBId", participante_id):
            return True

        if nome and self._existe_por_campo("equipeA", nome):
            return True

        if nome and self._existe_por_campo("equipeB", nome):
            return True

        return False

    def proximo_id(self) -> int:
        return self.database.next_sequence("confrontos", seed=self._ultimo_id())

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

    def _ultimo_id(self) -> int:
        documentos = self.collection.order_by("id", direction=Query.DESCENDING).limit(1).stream()
        for documento in documentos:
            dados = documento.to_dict() or {}
            return int(dados.get("id", 0))
        return 0

    def _existe_por_campo(self, campo: str, valor: int | str) -> bool:
        documentos = self.collection.where(filter=FieldFilter(campo, "==", valor)).limit(1).stream()
        for _ in documentos:
            return True
        return False

    def _count_query(self, query) -> int:
        try:
            resultado = query.count().get()
            if not resultado:
                return 0

            primeiro = resultado[0]
            agregado = primeiro[0] if isinstance(primeiro, (list, tuple)) else primeiro
            return int(getattr(agregado, "value", 0) or 0)
        except Exception:
            return sum(1 for _ in query.stream())
