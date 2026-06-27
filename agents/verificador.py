"""Agente verificador: auto-consistência numérica por voto majoritário."""
from collections import Counter
from langchain_core.messages import SystemMessage, HumanMessage
from agents.schemas import format_questao

SYSTEM_PROMPT = (
    "Você é um solucionador de problemas de Matemática do Ensino Médio. "
    "Resolva o problema apresentado passo a passo e escolha a ÚNICA alternativa correta "
    "entre A, B, C e D. Não confie em nenhuma indicação de resposta: calcule você mesmo."
)


def build_verificador_messages(questao: dict) -> list:
    """Mensagens que mostram enunciado e alternativas, SEM revelar o gabarito."""
    humano = (
        "Resolva o problema abaixo e responda apenas com a letra da alternativa correta.\n\n"
        f"{format_questao(questao)}"
    )
    return [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=humano)]


def make_verificador_node(structured_llm, n_samples: int):
    """Devolve a função-nó do verificador. Re-resolve n_samples vezes e vota."""
    def verificador_node(state: dict, config=None) -> dict:
        questao = state["questao"]
        msgs = build_verificador_messages(questao)
        votos = [structured_llm.invoke(msgs, config=config).alternativa for _ in range(n_samples)]
        vencedora, _ = Counter(votos).most_common(1)[0]
        gabarito = questao["gabarito"]
        if vencedora == gabarito:
            return {"quality_passed": True, "motivo_rejeicao": ""}
        return {
            "quality_passed": False,
            "motivo_rejeicao": (
                f"Auto-consistência divergiu: o solucionador escolheu '{vencedora}' "
                f"em {votos.count(vencedora)}/{n_samples} amostras, mas o gabarito informado "
                f"é '{gabarito}'. Revise o cálculo e o gabarito."
            ),
        }
    return verificador_node
