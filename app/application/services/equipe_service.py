from app.application.dtos.equipe_dto import EquipeInput
from app.domain.entities.equipe import Equipe, Membro
from app.domain.repositories.equipe_repository import EquipeRepository


class EquipeService:
    def __init__(self, repository: EquipeRepository) -> None:
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
            email=payload.email,
            modalidade=payload.modalidade,
            membros=[
                Membro(
                    id=item.id or self._proximo_id_membro(proximo_id, index),
                    nome=item.nome,
                    habilidades=item.habilidades,
                    funcao=item.funcao,
                )
                for index, item in enumerate(payload.membros, start=1)
            ],
            icone=payload.icone,
        )
        return self.repository.criar(equipe)

    def atualizar_equipe(self, equipe_id: int, payload: EquipeInput) -> Equipe | None:
        atual = self.repository.obter_por_id(equipe_id)
        if atual is None:
            return None

        equipe_atualizada = Equipe(
            id=equipe_id,
            nome=payload.nome,
            responsavel=payload.responsavel,
            email=payload.email,
            modalidade=payload.modalidade,
            membros=[
                Membro(
                    id=item.id or self._proximo_id_membro(equipe_id, index),
                    nome=item.nome,
                    habilidades=item.habilidades,
                    funcao=item.funcao,
                )
                for index, item in enumerate(payload.membros, start=1)
            ],
            icone=payload.icone,
        )
        return self.repository.atualizar(equipe_id, equipe_atualizada)

    def remover_equipe(self, equipe_id: int) -> bool:
        return self.repository.remover(equipe_id)

    def _proximo_id_equipe(self) -> int:
        equipes = self.repository.listar()
        return max((equipe.id for equipe in equipes), default=0) + 1

    @staticmethod
    def _proximo_id_membro(equipe_id: int, indice: int) -> int:
        return int(f"{equipe_id}{indice:02d}")
