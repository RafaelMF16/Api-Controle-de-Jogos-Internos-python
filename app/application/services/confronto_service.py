from app.application.dtos.confronto_dto import ConfrontoInput
from app.core.cache import MemoryCache
from app.core.config import Settings
from app.domain.entities.confronto import Confronto, PrevisaoConfronto, StatusConfronto
from app.domain.repositories.confronto_repository import ConfrontoRepository


class ConfrontoService:
    def __init__(self, repository: ConfrontoRepository, cache: MemoryCache, settings: Settings) -> None:
        self.repository = repository
        self.cache = cache
        self.settings = settings

    def listar_confrontos(
        self,
        busca: str | None = None,
        equipe: str | None = None,
        modalidade: str | None = None,
        status: StatusConfronto | None = None,
    ) -> list[Confronto]:
        confrontos = self._listar_todos_confrontos()

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
            confronto for confronto in self._listar_todos_confrontos()
            if confronto.status in {StatusConfronto.AGENDADO, StatusConfronto.AO_VIVO}
        ]

    def obter_confronto(self, confronto_id: int) -> Confronto | None:
        return self.repository.obter_por_id(confronto_id)

    def criar_confronto(self, payload: ConfrontoInput) -> Confronto:
        confronto = Confronto(
            id=self._proximo_id_confronto(),
            previsao=PrevisaoConfronto.pendente(),
            **payload.model_dump(),
        )
        criado = self.repository.criar(confronto)
        self._invalidar_cache()
        return criado

    def atualizar_confronto(self, confronto_id: int, payload: ConfrontoInput) -> Confronto | None:
        atual = self.repository.obter_por_id(confronto_id)
        if atual is None:
            return None

        alterou_base_previsao = (
            atual.equipeA != payload.equipeA
            or atual.equipeB != payload.equipeB
            or atual.modalidade != payload.modalidade
            or atual.participanteAId != payload.participanteAId
            or atual.participanteBId != payload.participanteBId
        )

        previsao = atual.previsao
        if alterou_base_previsao:
            previsao = previsao.model_copy(update={"precisaRegerar": True})

        confronto_atualizado = Confronto(
            id=confronto_id,
            previsao=previsao,
            **payload.model_dump(),
        )
        resultado = self.repository.atualizar(confronto_id, confronto_atualizado)
        self._invalidar_cache()
        return resultado

    def remover_confronto(self, confronto_id: int) -> bool:
        removeu = self.repository.remover(confronto_id)
        if removeu:
            self._invalidar_cache()
        return removeu

    def _proximo_id_confronto(self) -> int:
        confrontos = self._listar_todos_confrontos()
        return max((confronto.id for confronto in confrontos), default=0) + 1

    def _listar_todos_confrontos(self) -> list[Confronto]:
        return self.cache.get_or_set(
            "confrontos:list:all",
            self.settings.data_cache_ttl_seconds,
            self.repository.listar,
        )

    def _invalidar_cache(self) -> None:
        self.cache.invalidate_prefix("confrontos:")
        self.cache.invalidate_prefix("dashboard:")
