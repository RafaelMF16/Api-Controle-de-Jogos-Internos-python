import re
import unicodedata

# Lista de termos ofensivos em português e inglês comuns no contexto brasileiro.
# Inclui variações ortográficas relevantes.
_TERMOS_PROIBIDOS: list[str] = [
    # Xingamentos gerais
    "puta", "puto", "vadia", "vagabunda", "vagabundo", "safada", "safado",
    "piranha", "prostituta", "canalha", "corno", "corna", "cornao",
    "fdp", "filhadaputa", "filhodaputa", "desgraça", "desgraça", "desgraçado",
    "idiota", "imbecil", "babaca", "otario", "cretino", "burro", "retardado",
    "anta", "besta", "trouxa",
    # Termos sexuais explícitos
    "buceta", "xota", "xoxota", "ppk", "xereca", "boceta",
    "caralho", "pinto", "rola", "pau",
    "cuzao", "cuzão", "cú", "cu", "bunda",
    "foder", "fuder", "foda", "fudeu", "fodasse", "fodase",
    "sexo", "porno", "pornô", "putaria", "sacanagem",
    "gozar", "gozo", "tesao", "tesão",
    "vibrador", "dildo", "punheta",
    # Variações com números/substituições comuns
    "put4", "fud3", "c4ralho", "buc3ta",
    # Termos homofóbicos/discriminatórios
    "viado", "viadao", "viadão", "bicha", "traveco",
    "sapatao", "sapatão",
    # Inglês comum
    "fuck", "shit", "bitch", "asshole", "cunt", "dick", "pussy", "cock",
    "whore", "slut",
    # Compostos ofensivos com "filho" e "vai"
    "vaitomar", "tomano", "vtmnc", "vsf",
]

# Pré-compila: ordem decrescente de comprimento para evitar falsos positivos em substrings
_TERMOS_PROIBIDOS_SORTED = sorted(_TERMOS_PROIBIDOS, key=len, reverse=True)


def _normalizar(texto: str) -> str:
    """Remove acentos, converte para minúsculas e retira separadores típicos de username."""
    texto = texto.lower()
    # Remove acentos via NFKD
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    # Remove separadores comuns usados para disfarçar palavrões
    texto = re.sub(r"[._\-\s0-9]", "", texto)
    return texto


def contem_palavrao(texto: str) -> bool:
    """Retorna True se o texto contém algum termo ofensivo após normalização."""
    if not texto:
        return False
    normalizado = _normalizar(texto)
    return any(termo in normalizado for termo in _TERMOS_PROIBIDOS_SORTED)
