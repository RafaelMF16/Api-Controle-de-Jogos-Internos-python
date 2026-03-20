from app.application.dtos.dashboard_dto import ResumoDashboard
from app.domain.entities.confronto import StatusConfronto
from app.domain.repositories.confronto_repository import ConfrontoRepository
from app.domain.repositories.equipe_repository import EquipeRepository


class DashboardService:
    def __init__(
        self,
        equipe_repository: EquipeRepository,
        confronto_repository: ConfrontoRepository,
    ) -> None:
        self.equipe_repository = equipe_repository
        self.confronto_repository = confronto_repository

    def get_overview(self) -> ResumoDashboard:
        equipes = self.equipe_repository.listar()
        confrontos = self.confronto_repository.listar()
        proximos_confrontos = [
            confronto
            for confronto in confrontos
            if confronto.status != StatusConfronto.ENCERRADO
        ]

        return ResumoDashboard(
            totalEquipes=len(equipes),
            totalConfrontos=len(confrontos),
            proximosConfrontos=proximos_confrontos[:5],
        )
