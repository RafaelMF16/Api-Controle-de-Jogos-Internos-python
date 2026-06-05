from app.domain.entities.equipe import ModalidadeEquipe
from app.domain.entities.formato_modalidade import FormatoModalidade, GrupoConfig, PontuacaoConfig, TipoFormato
from app.domain.repositories.formato_modalidade_repository import FormatoModalidadeRepository
from app.infrastructure.persistence.firestore.firestore_client import FirestoreDatabase


class FirestoreFormatoModalidadeRepository(FormatoModalidadeRepository):
    def __init__(self, database: FirestoreDatabase) -> None:
        self.database = database

    @property
    def collection(self):
        return self.database.formatos_collection

    def listar(self) -> list[FormatoModalidade]:
        docs = self.collection.stream()
        return [self._doc_to_entity(doc.to_dict()) for doc in docs if doc.exists]

    def obter(self, modalidade: ModalidadeEquipe) -> FormatoModalidade | None:
        doc = self.collection.document(modalidade.value).get()
        if not doc.exists:
            return None
        return self._doc_to_entity(doc.to_dict())

    def salvar(self, formato: FormatoModalidade) -> FormatoModalidade:
        data = {
            "modalidade": formato.modalidade.value,
            "tipo": formato.tipo.value,
            "fases": formato.fases,
            "grupos": [{"nome": g.nome, "equipes": g.equipes} for g in formato.grupos],
            "pontuacao": {
                "vitoria": formato.pontuacao.vitoria,
                "empate": formato.pontuacao.empate,
                "derrota": formato.pontuacao.derrota,
            },
        }
        self.collection.document(formato.modalidade.value).set(data)
        return formato

    def remover(self, modalidade: ModalidadeEquipe) -> bool:
        doc_ref = self.collection.document(modalidade.value)
        if not doc_ref.get().exists:
            return False
        doc_ref.delete()
        return True

    def _doc_to_entity(self, data: dict) -> FormatoModalidade:
        pontuacao_raw = data.get("pontuacao") or {}
        grupos_raw = data.get("grupos") or []
        return FormatoModalidade(
            modalidade=ModalidadeEquipe(data["modalidade"]),
            tipo=TipoFormato(data["tipo"]),
            fases=data.get("fases") or [],
            grupos=[GrupoConfig(nome=g["nome"], equipes=g.get("equipes") or []) for g in grupos_raw],
            pontuacao=PontuacaoConfig(
                vitoria=pontuacao_raw.get("vitoria", 3),
                empate=pontuacao_raw.get("empate", 1),
                derrota=pontuacao_raw.get("derrota", 0),
            ),
        )
