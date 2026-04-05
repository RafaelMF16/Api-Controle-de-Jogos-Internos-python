from datetime import UTC, datetime

from app.application.services.prediction_provider import PredictionProvider
from app.domain.entities.confronto import Confronto, PrevisaoConfronto, StatusConfronto, StatusPrevisao
from app.domain.entities.equipe import Equipe, ModalidadeEquipe


class HeuristicPredictionProvider(PredictionProvider):
    def __init__(self, model_name: str = "heuristic-v1") -> None:
        self.model_name = model_name

    def gerar_previsao(
        self,
        confronto: Confronto,
        participante_a: Equipe | None,
        participante_b: Equipe | None,
        historico: list[Confronto],
    ) -> PrevisaoConfronto:
        score_a = 50.0
        score_b = 50.0

        historico_a = self._score_historico(confronto, confronto.equipeA, historico)
        historico_b = self._score_historico(confronto, confronto.equipeB, historico)
        score_a += historico_a
        score_b += historico_b

        score_a += self._score_participante(participante_a)
        score_b += self._score_participante(participante_b)

        score_a = max(score_a, 1)
        score_b = max(score_b, 1)

        total = score_a + score_b
        chance_a = round(score_a / total * 100)
        chance_b = 100 - chance_a

        favorito = confronto.equipeA if chance_a >= chance_b else confronto.equipeB

        return PrevisaoConfronto(
            status=StatusPrevisao.PRONTA,
            chanceA=chance_a,
            chanceB=chance_b,
            favorito=favorito,
            resumo=self._build_summary(confronto, participante_a, participante_b, historico_a, historico_b, favorito),
            modelo=self.model_name,
            geradaEm=datetime.now(UTC).isoformat(),
            precisaRegerar=False,
            erro=None,
        )

    def _score_historico(self, confronto: Confronto, nome_participante: str, historico: list[Confronto]) -> float:
        pontos = 0.0

        for item in historico:
            if item.id == confronto.id or item.modalidade != confronto.modalidade or item.status != StatusConfronto.ENCERRADO:
                continue

            participa = item.equipeA == nome_participante or item.equipeB == nome_participante
            if not participa:
                continue

            if item.vencedor:
                if item.vencedor == nome_participante:
                    pontos += 9
                else:
                    pontos -= 4
                continue

            if item.golsA is None or item.golsB is None:
                continue

            if item.golsA == item.golsB:
                pontos += 1
                continue

            vencedor = item.equipeA if item.golsA > item.golsB else item.equipeB
            pontos += 9 if vencedor == nome_participante else -4

        return max(min(pontos, 24), -12)

    def _score_participante(self, participante: Equipe | None) -> float:
        if participante is None:
            return 0.0

        if participante.modalidade == ModalidadeEquipe.NATACAO:
            score = float((participante.nivelTecnico or 3) * 6)
            experiencia = participante.experiencia or ""
            if experiencia:
                score += min(len(experiencia.split()), 12) * 0.4
            return score

        total_membros = len(participante.membros)
        habilidades = {habilidade.strip().lower() for membro in participante.membros for habilidade in membro.habilidades if habilidade.strip()}
        nivel_equipe = float((participante.nivelEquipe or 3) * 5)
        score_elenco = min(total_membros * 1.3, 10) + min(len(habilidades), 6)
        return nivel_equipe + score_elenco

    def _build_summary(
        self,
        confronto: Confronto,
        participante_a: Equipe | None,
        participante_b: Equipe | None,
        historico_a: float,
        historico_b: float,
        favorito: str,
    ) -> str:
        motivos: list[str] = []

        if historico_a != historico_b:
            motivos.append("o historico recente na modalidade pesa a favor do favorito")

        if confronto.modalidade == ModalidadeEquipe.NATACAO:
            nivel_a = participante_a.nivelTecnico if participante_a else None
            nivel_b = participante_b.nivelTecnico if participante_b else None
            if nivel_a != nivel_b:
                motivos.append("o nivel tecnico informado cria uma vantagem inicial")
            elif (participante_a and participante_a.experiencia) or (participante_b and participante_b.experiencia):
                motivos.append("a experiencia declarada ajuda a diferenciar os atletas")
        else:
            nivel_a = participante_a.nivelEquipe if participante_a else None
            nivel_b = participante_b.nivelEquipe if participante_b else None
            if nivel_a != nivel_b:
                motivos.append("o nivel da equipe influencia a projecao")
            membros_a = len(participante_a.membros) if participante_a else 0
            membros_b = len(participante_b.membros) if participante_b else 0
            if membros_a != membros_b:
                motivos.append("a profundidade do elenco influencia a projecao")

        if not motivos:
            motivos.append("os dados cadastrados indicam confronto equilibrado")

        return f"{favorito} aparece levemente a frente porque {motivos[0]}."
