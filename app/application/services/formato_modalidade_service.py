from app.application.dtos.formato_modalidade_dto import FormatoModalidadeInput
from app.core.cache import MemoryCache
from app.domain.entities.equipe import ModalidadeEquipe
from app.domain.entities.formato_modalidade import FormatoModalidade
from app.domain.repositories.formato_modalidade_repository import FormatoModalidadeRepository


class FormatoModalidadeService:
    def __init__(self, repository: FormatoModalidadeRepository, cache: MemoryCache) -> None:
        self.repository = repository
        self.cache = cache

    def listar(self) -> list[FormatoModalidade]:
        return self.cache.get_or_set("formatos:list", 300, self.repository.listar)

    def obter(self, modalidade: ModalidadeEquipe) -> FormatoModalidade | None:
        return self.cache.get_or_set(
            f"formatos:{modalidade.value}",
            300,
            lambda: self.repository.obter(modalidade),
        )

    def salvar(self, modalidade: ModalidadeEquipe, payload: FormatoModalidadeInput) -> FormatoModalidade:
        formato = FormatoModalidade(
            modalidade=modalidade,
            tipo=payload.tipo,
            fases=payload.fases,
            grupos=payload.grupos,
            pontuacao=payload.pontuacao,
        )
        salvo = self.repository.salvar(formato)
        self._invalidar_cache(modalidade)
        return salvo

    def remover(self, modalidade: ModalidadeEquipe) -> bool:
        removeu = self.repository.remover(modalidade)
        if removeu:
            self._invalidar_cache(modalidade)
        return removeu

    def _invalidar_cache(self, modalidade: ModalidadeEquipe) -> None:
        self.cache.invalidate_prefix("formatos:")
        self.cache.invalidate_prefix(f"ranking:{modalidade.value}")
