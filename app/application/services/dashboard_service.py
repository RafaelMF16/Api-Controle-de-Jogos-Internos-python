from app.application.dtos.dashboard_dto import ResumoDashboard
from app.core.cache import MemoryCache
from app.core.config import Settings
from app.domain.entities.confronto import StatusConfronto
from app.domain.repositories.confronto_repository import ConfrontoRepository
from app.domain.repositories.equipe_repository import EquipeRepository


class DashboardService:
    def __init__(
        self,
        equipe_repository: EquipeRepository,
        confronto_repository: ConfrontoRepository,
        cache: MemoryCache,
        settings: Settings,
    ) -> None:
        self.equipe_repository = equipe_repository
        self.confronto_repository = confronto_repository
        self.cache = cache
        self.settings = settings

    def get_overview(self) -> ResumoDashboard:
        return self.cache.get_or_set(
            "dashboard:overview",
            self.settings.dashboard_cache_ttl_seconds,
            self._build_overview,
        )

    def _build_overview(self) -> ResumoDashboard:
        return ResumoDashboard(
            totalEquipes=self.equipe_repository.contar(),
            totalConfrontos=self.confronto_repository.contar(),
            proximosConfrontos=[
                confronto
                for confronto in self.confronto_repository.listar_proximos(limit=5)
                if confronto.status != StatusConfronto.ENCERRADO
            ][:5],
        )
