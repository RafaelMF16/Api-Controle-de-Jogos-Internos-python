import json
from datetime import UTC, datetime

from app.application.services.prediction_provider import PredictionProvider
from app.domain.entities.confronto import Confronto, PrevisaoConfronto, StatusPrevisao
from app.domain.entities.equipe import Equipe


class VertexPredictionProvider(PredictionProvider):
    def __init__(self, project_id: str, location: str, model_name: str) -> None:
        self.project_id = project_id
        self.location = location
        self.model_name = model_name

    def gerar_previsao(
        self,
        confronto: Confronto,
        participante_a: Equipe | None,
        participante_b: Equipe | None,
        historico: list[Confronto],
    ) -> PrevisaoConfronto:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError(
                "A dependencia google-genai nao esta instalada. Execute pip install -r requirements.txt."
            ) from exc

        client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location,
        )

        prompt = self._build_prompt(confronto, participante_a, participante_b, historico)
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )

        payload = self._extract_payload(response)
        chance_a = self._normalize_percentage(payload.get("chanceA"))
        chance_b = self._normalize_percentage(payload.get("chanceB"))
        favorito = str(payload.get("favorito") or "").strip() or (confronto.equipeA if chance_a >= chance_b else confronto.equipeB)
        resumo = str(payload.get("resumo") or "").strip() or "A IA gerou uma previsão com base nos dados cadastrados."

        return PrevisaoConfronto(
            status=StatusPrevisao.PRONTA,
            chanceA=chance_a,
            chanceB=chance_b,
            favorito=favorito,
            resumo=resumo,
            modelo=self.model_name,
            geradaEm=datetime.now(UTC).isoformat(),
            precisaRegerar=False,
            erro=None,
        )

    def _build_prompt(
        self,
        confronto: Confronto,
        participante_a: Equipe | None,
        participante_b: Equipe | None,
        historico: list[Confronto],
    ) -> str:
        contexto = {
            "modalidade": confronto.modalidade.value if hasattr(confronto.modalidade, "value") else str(confronto.modalidade),
            "participanteA": self._serialize_participante(confronto.equipeA, participante_a),
            "participanteB": self._serialize_participante(confronto.equipeB, participante_b),
            "historicoRelacionandoModalidade": [
                {
                    "equipeA": item.equipeA,
                    "equipeB": item.equipeB,
                    "modalidade": item.modalidade.value if hasattr(item.modalidade, "value") else str(item.modalidade),
                    "status": item.status.value if hasattr(item.status, "value") else str(item.status),
                    "golsA": item.golsA,
                    "golsB": item.golsB,
                    "vencedor": item.vencedor,
                }
                for item in historico
                if item.modalidade == confronto.modalidade
            ],
        }

        return (
            "Voce e um analista esportivo. Avalie o confronto usando apenas os dados fornecidos. "
            "Retorne somente JSON valido, sem markdown, sem comentarios e sem texto extra. "
            "O JSON deve ter exatamente estas chaves: chanceA, chanceB, favorito, resumo. "
            "chanceA e chanceB devem ser inteiros que somam 100. "
            "favorito deve ser exatamente o nome de um dos participantes. "
            "resumo deve ter no maximo 220 caracteres e explicar brevemente a previsao.\n\n"
            f"DADOS:\n{json.dumps(contexto, ensure_ascii=False)}"
        )

    def _serialize_participante(self, nome: str, participante: Equipe | None) -> dict:
        if participante is None:
            return {"nome": nome}

        return {
            "nome": participante.nome,
            "curso": participante.curso,
            "periodo": participante.periodo,
            "modalidade": participante.modalidade.value if hasattr(participante.modalidade, "value") else str(participante.modalidade),
            "totalMembros": len(participante.membros),
            "membros": [
                {
                    "nome": membro.nome,
                    "funcao": membro.funcao,
                    "habilidades": membro.habilidades,
                    "nivel": membro.nivel,
                    "especialidade": membro.especialidade,
                }
                for membro in participante.membros
            ],
        }

    def _extract_payload(self, response: object) -> dict:
        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Vertex AI retornou resposta vazia.")

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Vertex AI retornou JSON invalido: {text}") from exc

        if not isinstance(payload, dict):
            raise RuntimeError("Vertex AI retornou um formato invalido para a previsao.")

        return payload

    def _normalize_percentage(self, value: object) -> int:
        try:
            number = int(round(float(value)))
        except (TypeError, ValueError) as exc:
            raise RuntimeError("Vertex AI nao retornou percentuais validos.") from exc

        return min(max(number, 0), 100)
