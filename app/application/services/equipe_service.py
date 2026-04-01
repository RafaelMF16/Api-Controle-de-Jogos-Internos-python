from app.application.dtos.equipe_dto import EquipeInput
from app.domain.entities.equipe import Equipe, Membro, ModalidadeEquipe
from app.domain.repositories.equipe_repository import EquipeRepository


class EquipeService:
    def __init__(self, repository: EquipeRepository):
        self.repository = repository

    def listar_equipes(self) -> list[Equipe]:
        return self.repository.listar()

    def obter_equipe(self, equipe_id: int) -> Equipe | None:
        return self.repository.obter_por_id(equipe_id)

    def criar_equipe(self, payload: EquipeInput) -> Equipe:
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
        )
        self.repository.criar(equipe)
        return equipe

    def atualizar_equipe(self, equipe_id: int, payload: EquipeInput) -> Equipe | None:
        atual = self.repository.obter_por_id(equipe_id)
        if atual is None:
            return None

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
        )
        self.repository.atualizar(equipe_id, equipe)
        return equipe

    def remover_equipe(self, equipe_id: int) -> bool:
        return self.repository.remover(equipe_id)

    def obter_inscricao_individual(self, usuario_id: int, modalidade: ModalidadeEquipe) -> Equipe | None:
        for equipe in self.repository.listar():
            if equipe.usuarioId == usuario_id and equipe.modalidade == modalidade:
                return equipe
        return None

    def _proximo_id_equipe(self) -> int:
        equipes = self.repository.listar()
        return max((equipe.id for equipe in equipes), default=0) + 1

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
