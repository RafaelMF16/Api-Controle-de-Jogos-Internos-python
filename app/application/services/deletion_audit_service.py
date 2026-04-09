from datetime import UTC, datetime
from typing import Any

from app.domain.entities.usuario import Usuario
from app.infrastructure.persistence.firestore.firestore_client import FirestoreDatabase


class DeletionAuditService:
    def __init__(self, database: FirestoreDatabase) -> None:
        self.collection = database.auditoria_delecoes_collection

    def registrar(
        self,
        *,
        ator: Usuario,
        entidade_tipo: str,
        entidade_id: int,
        entidade_nome: str | None = None,
        detalhes: dict[str, Any] | None = None,
    ) -> bool:
        try:
            self.collection.add(
                {
                    "acao": "delete",
                    "entidadeTipo": entidade_tipo,
                    "entidadeId": entidade_id,
                    "entidadeNome": entidade_nome,
                    "atorId": ator.id,
                    "atorNome": ator.nome,
                    "atorUsername": ator.username,
                    "atorRole": ator.role.value,
                    "criadoEm": datetime.now(UTC).isoformat(),
                    "detalhes": detalhes or {},
                }
            )
            return True
        except Exception:
            return False
