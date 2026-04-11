from google.cloud.firestore_v1 import FieldFilter, Query

from app.application.dtos.cursor_pagination_dto import CursorPaginatedResponse
from app.domain.entities.equipe import ATLETA_FUNCAO, CAPITAO_FUNCAO, Equipe
from app.domain.entities.equipe import ModalidadeEquipe
from app.domain.repositories.equipe_repository import EquipeRepository
from app.infrastructure.persistence.firestore.firestore_client import FirestoreDatabase


class FirestoreEquipeRepository(EquipeRepository):
    def __init__(self, database: FirestoreDatabase) -> None:
        self.database = database
        self.collection = database.equipes_collection

    def listar(self) -> list[Equipe]:
        documentos = self.collection.order_by("id").stream()
        return [self._to_equipe(documento.to_dict()) for documento in documentos]

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

            equipe = self._to_equipe(dados)
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
        return self._to_equipe(documento.to_dict())

    def obter_por_nome_modalidade(self, nome: str, modalidade: str) -> Equipe | None:
        nome_normalizado = self._normalizar_nome(nome)
        documentos = self.collection.where(
            filter=FieldFilter("nomeNormalizado", "==", nome_normalizado)
        ).where(
            filter=FieldFilter("modalidade", "==", modalidade)
        ).limit(1).stream()
        for documento in documentos:
            return self._to_equipe(documento.to_dict())

        documentos_legados = self.collection.where(
            filter=FieldFilter("modalidade", "==", modalidade)
        ).limit(50).stream()
        for documento in documentos_legados:
            equipe = self._to_equipe(documento.to_dict())
            if self._normalizar_nome(equipe.nome) == nome_normalizado:
                return equipe
        return None

    def obter_inscricao_individual(self, usuario_id: int, modalidade: str) -> Equipe | None:
        documentos = self.collection.where(
            filter=FieldFilter("usuarioId", "==", usuario_id)
        ).where(
            filter=FieldFilter("modalidade", "==", modalidade)
        ).limit(1).stream()
        for documento in documentos:
            return self._to_equipe(documento.to_dict())
        return None

    def existe_vinculo_usuario(self, usuario_id: int) -> bool:
        documentos = self.collection.where(filter=FieldFilter("usuarioId", "==", usuario_id)).limit(1).stream()
        for _ in documentos:
            return True
        return False

    def proximo_id(self) -> int:
        return self.database.next_sequence("equipes", seed=self._ultimo_id())

    def criar(self, equipe: Equipe) -> Equipe:
        dados = equipe.model_dump(mode="json")
        dados["nomeNormalizado"] = self._normalizar_nome(equipe.nome)
        self.collection.document(str(equipe.id)).set(dados)
        return equipe

    def atualizar(self, equipe_id: int, equipe: Equipe) -> Equipe | None:
        referencia = self.collection.document(str(equipe_id))
        if not referencia.get().exists:
            return None

        dados = equipe.model_dump(mode="json")
        dados["nomeNormalizado"] = self._normalizar_nome(equipe.nome)
        referencia.set(dados)
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
    def _normalizar_nome(nome: str) -> str:
        return " ".join((nome or "").strip().lower().split())

    @staticmethod
    def _to_equipe(dados: dict | None) -> Equipe:
        return Equipe.model_validate(FirestoreEquipeRepository._normalizar_dados_legados(dados or {}))

    @staticmethod
    def _normalizar_dados_legados(dados: dict) -> dict:
        if dados.get("modalidade") == ModalidadeEquipe.NATACAO.value:
            dados["responsavel"] = None
            membros_brutos = dados.get("membros") or []
            base_id = int(dados.get("id", 0) or 0) * 1000
            atletas = []

            for index, membro in enumerate(membros_brutos[:1], start=1):
                if not isinstance(membro, dict):
                    continue

                atleta_normalizado = dict(membro)
                atleta_normalizado["id"] = atleta_normalizado.get("id") or (base_id + index)
                atleta_normalizado["nome"] = atleta_normalizado.get("nome") or dados.get("nome")
                atleta_normalizado["funcao"] = ATLETA_FUNCAO
                atleta_normalizado["usuarioId"] = atleta_normalizado.get("usuarioId", dados.get("usuarioId"))
                atleta_normalizado["habilidades"] = [
                    habilidade.strip()
                    for habilidade in (atleta_normalizado.get("habilidades") or [])
                    if isinstance(habilidade, str) and habilidade.strip()
                ][:3]
                atleta_normalizado["nivel"] = (atleta_normalizado.get("nivel") or "").strip() or None
                atleta_normalizado["especialidade"] = (atleta_normalizado.get("especialidade") or "").strip() or None
                atletas.append(atleta_normalizado)

            if not atletas:
                atletas.append(
                    {
                        "id": base_id + 1,
                        "nome": dados.get("nome"),
                        "habilidades": [],
                        "funcao": ATLETA_FUNCAO,
                        "nivel": None,
                        "especialidade": None,
                        "usuarioId": dados.get("usuarioId"),
                    }
                )

            dados["membros"] = atletas
            return dados

        membros_brutos = dados.get("membros") or []
        membros_normalizados: list[dict] = []
        capitao_encontrado = False
        base_id = int(dados.get("id", 0) or 0) * 1000

        for index, membro in enumerate(membros_brutos, start=1):
            if not isinstance(membro, dict):
                continue

            membro_normalizado = dict(membro)
            membro_normalizado["habilidades"] = [
                habilidade.strip()
                for habilidade in (membro_normalizado.get("habilidades") or [])
                if isinstance(habilidade, str) and habilidade.strip()
            ][:3]
            membro_normalizado["id"] = membro_normalizado.get("id") or (base_id + index)

            if (membro_normalizado.get("funcao") or "").strip().lower() == CAPITAO_FUNCAO.lower():
                capitao_encontrado = True

            membros_normalizados.append(membro_normalizado)

        if not capitao_encontrado and dados.get("responsavel"):
            membros_normalizados.insert(
                0,
                {
                    "id": base_id + 1,
                    "nome": dados["responsavel"],
                    "habilidades": [],
                    "funcao": CAPITAO_FUNCAO,
                    "usuarioId": None,
                },
            )

        dados["membros"] = membros_normalizados
        if not dados.get("responsavel") and membros_normalizados:
            dados["responsavel"] = membros_normalizados[0].get("nome")

        return dados

    @staticmethod
    def _categoria_confere(equipe: Equipe, categoria: str | None) -> bool:
        if categoria == "individual":
            return equipe.modalidade == ModalidadeEquipe.NATACAO

        if categoria == "coletivo":
            return equipe.modalidade != ModalidadeEquipe.NATACAO

        return True
