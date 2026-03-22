from app.application.dtos.confronto_dto import ConfrontoInput
from app.domain.entities.confronto import Confronto, StatusConfronto
from app.domain.repositories.confronto_repository import ConfrontoRepository


class ConfrontoService:
    def __init__(self, repository: ConfrontoRepository) -> None:
        self.repository = repository

    def listar_confrontos(
        self,
        busca: str | None = None,
        equipe: str | None = None,
        modalidade: str | None = None,
        status: StatusConfronto | None = None,
    ) -> list[Confronto]:
        confrontos = self.repository.listar()

        if busca:
            termo = busca.strip().lower()
            confrontos = [
                confronto for confronto in confrontos
                if termo in confronto.equipeA.lower() or termo in confronto.equipeB.lower()
            ]

        if equipe:
            confrontos = [
                confronto for confronto in confrontos
                if confronto.equipeA.lower() == equipe.lower() or confronto.equipeB.lower() == equipe.lower()
            ]

        if modalidade:
            confrontos = [
                confronto for confronto in confrontos
                if (confronto.modalidade or "").lower() == modalidade.lower()
            ]

        if status:
            confrontos = [confronto for confronto in confrontos if confronto.status == status]

        return confrontos

    def listar_proximos_confrontos(self) -> list[Confronto]:
        return [
            confronto for confronto in self.repository.listar()
            if confronto.status in {StatusConfronto.AGENDADO, StatusConfronto.AO_VIVO}
        ]

    def obter_confronto(self, confronto_id: int) -> Confronto | None:
        return self.repository.obter_por_id(confronto_id)

    def criar_confronto(self, payload: ConfrontoInput) -> Confronto:
        confronto = Confronto(id=self._proximo_id_confronto(), **payload.model_dump())
        return self.repository.criar(confronto)

    def atualizar_confronto(self, confronto_id: int, payload: ConfrontoInput) -> Confronto | None:
        atual = self.repository.obter_por_id(confronto_id)
        if atual is None:
            return None

        confronto_atualizado = Confronto(id=confronto_id, **payload.model_dump())
        return self.repository.atualizar(confronto_id, confronto_atualizado)

    def remover_confronto(self, confronto_id: int) -> bool:
        return self.repository.remover(confronto_id)

    def _proximo_id_confronto(self) -> int:
        confrontos = self.repository.listar()
        return max((confronto.id for confronto in confrontos), default=0) + 1
