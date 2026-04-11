from fastapi import HTTPException, status

from app.application.dtos.cursor_pagination_dto import CursorPaginatedResponse
from app.application.dtos.equipe_dto import EquipeInput
from app.core.cache import MemoryCache
from app.core.config import Settings
from app.domain.entities.equipe import CAPITAO_FUNCAO, MAX_HABILIDADES_POR_MEMBRO, Equipe, Membro, ModalidadeEquipe, eh_membro_capitao, obter_limite_integrantes
from app.domain.repositories.confronto_repository import ConfrontoRepository
from app.domain.repositories.equipe_repository import EquipeRepository
from app.domain.repositories.usuario_repository import UsuarioRepository


class EquipeService:
    def __init__(
        self,
        repository: EquipeRepository,
        cache: MemoryCache,
        settings: Settings,
        confronto_repository: ConfrontoRepository,
        usuario_repository: UsuarioRepository,
    ):
        self.repository = repository
        self.cache = cache
        self.settings = settings
        self.confronto_repository = confronto_repository
        self.usuario_repository = usuario_repository

    def listar_equipes_paginado(
        self,
        *,
        categoria: str | None = None,
        limit: int = 10,
        cursor: str | None = None,
    ) -> CursorPaginatedResponse[Equipe]:
        return self.repository.listar_paginado(
            categoria=categoria,
            limit=limit,
            cursor=cursor,
        )

    def obter_equipe(self, equipe_id: int) -> Equipe | None:
        return self.repository.obter_por_id(equipe_id)

    def criar_equipe(self, payload: EquipeInput) -> Equipe:
        self._garantir_nome_disponivel(payload.nome, payload.modalidade)
        proximo_id = self._proximo_id_equipe()
        equipe = Equipe(
            id=proximo_id,
            nome=payload.nome.strip(),
            responsavel=payload.responsavel,
            curso=payload.curso or "",
            periodo=payload.periodo or "",
            modalidade=payload.modalidade,
            membros=self._montar_membros(payload, proximo_id),
            usuarioId=payload.usuarioId,
            icone=payload.icone,
        )
        self._validar_limites_e_consistencia(equipe)
        self.repository.criar(equipe)
        self._invalidar_cache()
        return equipe

    def atualizar_equipe(self, equipe_id: int, payload: EquipeInput) -> Equipe | None:
        atual = self.repository.obter_por_id(equipe_id)
        if atual is None:
            return None

        self._garantir_nome_disponivel(payload.nome, payload.modalidade, equipe_id)
        equipe = Equipe(
            id=equipe_id,
            nome=payload.nome.strip(),
            responsavel=payload.responsavel,
            curso=payload.curso or "",
            periodo=payload.periodo or "",
            modalidade=payload.modalidade,
            membros=self._montar_membros(payload, equipe_id),
            usuarioId=payload.usuarioId,
            icone=payload.icone,
        )
        self._validar_limites_e_consistencia(equipe)
        self.repository.atualizar(equipe_id, equipe)
        self._invalidar_cache()
        return equipe

    def remover_equipe(self, equipe_id: int) -> Equipe | None:
        equipe = self.repository.obter_por_id(equipe_id)
        if equipe is None:
            return None

        if self.confronto_repository.existe_com_participante(equipe_id, equipe.nome):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Nao e possivel remover este cadastro porque existem confrontos vinculados a ele.",
            )

        removeu = self.repository.remover(equipe_id)
        if removeu:
            self.usuario_repository.desvincular_equipe(equipe_id)
            self._invalidar_cache()
            self.cache.invalidate_prefix("usuarios:")
            return equipe
        return None

    def obter_inscricao_individual(self, usuario_id: int, modalidade: ModalidadeEquipe) -> Equipe | None:
        return self.repository.obter_inscricao_individual(usuario_id, modalidade.value)

    def _garantir_nome_disponivel(
        self,
        nome: str,
        modalidade: ModalidadeEquipe,
        equipe_id_atual: int | None = None,
    ) -> None:
        if modalidade == ModalidadeEquipe.NATACAO:
            return

        existente = self.repository.obter_por_nome_modalidade(nome.strip(), modalidade.value)
        if existente is not None and existente.id != equipe_id_atual:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ja existe uma equipe cadastrada com este nome.",
            )

    def _proximo_id_equipe(self) -> int:
        return self.repository.proximo_id()

    def _invalidar_cache(self) -> None:
        self.cache.invalidate_prefix("equipes:")
        self.cache.invalidate_prefix("dashboard:")

    def _montar_membros(self, payload: EquipeInput, equipe_id: int) -> list[Membro]:
        return [
            Membro(
                id=item.id or (equipe_id * 1000 + index),
                nome=item.nome,
                habilidades=item.habilidades,
                funcao=item.funcao,
                nivel=item.nivel,
                especialidade=item.especialidade,
                usuarioId=item.usuarioId,
            )
            for index, item in enumerate(payload.membros, start=1)
        ]

    def _validar_limites_e_consistencia(self, equipe: Equipe) -> None:
        if equipe.modalidade == ModalidadeEquipe.NATACAO:
            if len(equipe.membros) != 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Inscricoes individuais precisam ter exatamente um atleta principal.",
                )

            atleta = equipe.membros[0]
            if not atleta.nivel:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Informe o nivel do atleta na inscricao individual.",
                )

            if not atleta.especialidade:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Informe a especialidade do atleta na inscricao individual.",
                )

            return

        limite = obter_limite_integrantes(equipe.modalidade)
        if len(equipe.membros) > limite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A modalidade {equipe.modalidade.value} permite no maximo {limite} integrantes.",
            )

        capitaes = [membro for membro in equipe.membros if eh_membro_capitao(membro)]
        if len(capitaes) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A equipe precisa ter exatamente um membro com funcao de Capitao.",
            )

        for membro in equipe.membros:
            if len(membro.habilidades) > MAX_HABILIDADES_POR_MEMBRO:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cada integrante pode ter no maximo {MAX_HABILIDADES_POR_MEMBRO} habilidades.",
                )

        equipe.responsavel = capitaes[0].nome
