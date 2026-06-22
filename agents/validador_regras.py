"""Agente determinístico: checa falhas estruturais (item-writing flaws) sem LLM."""
import config

_EXPRESSOES_PROIBIDAS = (
    "todas as anteriores",
    "nenhuma das anteriores",
    "todas as alternativas",
    "n.d.a",
)
_TERMOS_ABSOLUTOS = ("sempre", "nunca", "jamais", "todo ", "toda ")


def _alternativas(questao: dict) -> dict:
    return {
        "A": questao.get("alternativa_a", ""),
        "B": questao.get("alternativa_b", ""),
        "C": questao.get("alternativa_c", ""),
        "D": questao.get("alternativa_d", ""),
    }


def validar_regras(questao: dict, checar_termos_absolutos: bool = False) -> tuple[bool, str]:
    """Retorna (passou, motivo). Motivo vazio quando passou."""
    alternativas = _alternativas(questao)

    # Regra 1: gabarito válido
    gabarito = questao.get("gabarito")
    if gabarito not in {"A", "B", "C", "D"}:
        return False, f"Gabarito inválido: {gabarito!r} (esperado A, B, C ou D)."

    # Regra 2: alternativa vazia
    for letra, texto in alternativas.items():
        if not texto or not texto.strip():
            return False, f"Alternativa {letra} está vazia."

    # Regra 3: alternativas duplicadas
    normalizadas = [t.strip().lower() for t in alternativas.values()]
    if len(set(normalizadas)) < len(normalizadas):
        return False, "Há alternativas duplicadas."

    # Regra 4: 'todas/nenhuma das anteriores'
    for letra, texto in alternativas.items():
        baixo = texto.strip().lower()
        if any(expr in baixo for expr in _EXPRESSOES_PROIBIDAS):
            return False, f"Alternativa {letra} usa expressão proibida (ex.: 'todas as anteriores')."

    # Regra 5: alternativa correta muito mais longa (pista de tamanho)
    correta_len = len(alternativas[gabarito].strip())
    outras = [len(alternativas[l].strip()) for l in alternativas if l != gabarito]
    media_outras = sum(outras) / len(outras) if outras else 0
    if media_outras > 0 and correta_len > 1.5 * media_outras:
        return False, "Alternativa correta é muito mais longa que as demais (pista de tamanho)."

    # Regra 6 (opcional): termos absolutos
    if checar_termos_absolutos:
        texto_completo = (
            questao.get("enunciado", "") + " " + " ".join(alternativas.values())
        ).lower()
        for termo in _TERMOS_ABSOLUTOS:
            if termo in texto_completo:
                return False, f"Uso de termo absoluto ('{termo.strip()}')."

    return True, ""


def make_validador_regras_node():
    """Devolve a função-nó do validador de regras."""
    def validador_regras_node(state: dict) -> dict:
        passou, motivo = validar_regras(
            state["questao"],
            checar_termos_absolutos=config.REGRA_TERMOS_ABSOLUTOS,
        )
        return {
            "regras_passed": passou,
            "motivo_rejeicao": "" if passou else motivo,
        }
    return validador_regras_node
