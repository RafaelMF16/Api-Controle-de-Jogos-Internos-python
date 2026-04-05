from fastapi import HTTPException, status

from app.application.dtos.equipe_dto import EquipeInput
from app.core.cache import MemoryCache
from app.core.config import Settings
from app.domain.entities.equipe import Equipe, Membro, ModalidadeEquipe
from app.domain.repositories.equipe_repository import EquipeRepository


class EquipeService:
    def __init__(self, repository: EquipeRepository, cache: MemoryCache, settings: Settings):
        self.repository = repository
        self.cache = cache
        self.settings = settings

    def listar_equipes(self, categoria: str | None = None) -> list[Equipe]:
        equipes = self._listar_todas_equipes()

        if categoria == "individual":
            return [equipe for equipe in equipes if equipe.modalidade == ModalidadeEquipe.NATACAO]

        if categoria == "coletivo":
            return [equipe for equipe in equipes if equipe.modalidade != ModalidadeEquipe.NATACAO]

        return equipes

    def obter_equipe(self, equipe_id: int) -> Equipe | None:
        return self.repository.obter_por_id(equipe_id)

    def criar_equipe(self, payload: EquipeInput) -> Equipe:
        self._garantir_nome_disponivel(payload.nome, payload.modalidade)
        proximo_id = self._proximo_id_equipe()
        equipe = Equipe(
            id=proximo_id,
            nome=payload.nome,
            responsavel=payload.responsavel,
            curso=payload.curso or "",
            periodo=payload.periodo or "",
            modalidade=payload.modalidade,
            membros=self._montar_membros(payload, proximo_id),
            usuarioId=payload.usuarioId,
            icone=payload.icone,
            nivelTecnico=payload.nivelTecnico,
            nivelEquipe=payload.nivelEquipe,
            experiencia=payload.experiencia,
        )
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
            nome=payload.nome,
            responsavel=payload.responsavel,
            curso=payload.curso or "",
            periodo=payload.periodo or "",
            modalidade=payload.modalidade,
            membros=self._montar_membros(payload, equipe_id),
            usuarioId=payload.usuarioId,
            icone=payload.icone,
            nivelTecnico=payload.nivelTecnico,
            nivelEquipe=payload.nivelEquipe,
            experiencia=payload.experiencia,
        )
        self.repository.atualizar(equipe_id, equipe)
        self._invalidar_cache()
        return equipe

    def remover_equipe(self, equipe_id: int) -> bool:
        removeu = self.repository.remover(equipe_id)
        if removeu:
            self._invalidar_cache()
        return removeu

    def obter_inscricao_individual(self, usuario_id: int, modalidade: ModalidadeEquipe) -> Equipe | None:
        for equipe in self._listar_todas_equipes():
            if equipe.usuarioId == usuario_id and equipe.modalidade == modalidade:
                return equipe
        return None

    def _garantir_nome_disponivel(
        self,
        nome: str,
        modalidade: ModalidadeEquipe,
        equipe_id_atual: int | None = None,
    ) -> None:
        if modalidade == ModalidadeEquipe.NATACAO:
            return

        nome_normalizado = nome.strip().lower()
        for equipe in self._listar_todas_equipes():
            if equipe.modalidade == ModalidadeEquipe.NATACAO:
                continue

            if equipe_id_atual is not None and equipe.id == equipe_id_atual:
                continue

            if equipe.nome.strip().lower() == nome_normalizado:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ja existe uma equipe cadastrada com este nome.",
                )

    def _proximo_id_equipe(self) -> int:
        equipes = self._listar_todas_equipes()
        return max((equipe.id for equipe in equipes), default=0) + 1

    def _listar_todas_equipes(self) -> list[Equipe]:
        return self.cache.get_or_set(
            "equipes:list:all",
            self.settings.data_cache_ttl_seconds,
            self.repository.listar,
        )

    def _invalidar_cache(self) -> None:
        self.cache.invalidate_prefix("equipes:")
        self.cache.invalidate_prefix("dashboard:")

    def _montar_membros(self, payload: EquipeInput, equipe_id: int) -> list[Membro]:
        if payload.modalidade == ModalidadeEquipe.NATACAO:
            return []

        return [
            Membro(
                id=item.id or (equipe_id * 1000 + index),
                nome=item.nome,
                habilidades=item.habilidades,
                funcao=item.funcao,
            )
            for index, item in enumerate(payload.membros, start=1)
        ]
