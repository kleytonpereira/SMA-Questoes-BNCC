"""Agente Avaliador: aprova ou rejeita a questão gerada."""
from langchain_core.messages import SystemMessage, HumanMessage
from agents.schemas import format_questao

SYSTEM_PROMPT = (
    "Você é um revisor matemático rigoroso de questões para o Ensino Médio brasileiro.\n\n"
    "PASSO 1 — RESOLVA O PROBLEMA VOCÊ MESMO:\n"
    "Antes de qualquer julgamento, resolva o problema do zero, passo a passo, "
    "mostrando todos os cálculos. Não confie na explicação fornecida.\n\n"
    "PASSO 2 — COMPARE COM O GABARITO:\n"
    "Verifique se sua resposta coincide com o gabarito informado. "
    "Se não coincidir, a questão deve ser REPROVADA.\n\n"
    "PASSO 3 — VERIFIQUE AS ALTERNATIVAS:\n"
    "Confirme que cada alternativa errada é de fato incorreta e que "
    "não existe ambiguidade entre as opções.\n\n"
    "PASSO 4 — AVALIE OS CRITÉRIOS PEDAGÓGICOS:\n"
    "1. O gabarito é a ÚNICA alternativa correta.\n"
    "2. As alternativas erradas são plausíveis (erros comuns do aluno).\n"
    "3. A linguagem é adequada ao Ensino Médio.\n"
    "4. A questão corresponde ao tema solicitado.\n"
    "5. O enunciado é claro e sem ambiguidade.\n"
    "6. A questão NÃO é tautológica nem trivial: exige cálculo ou raciocínio real e o "
    "enunciado não contém a própria resposta.\n\n"
    "Só aprove (quality_passed=true) se TODOS os critérios forem atendidos E "
    "seu próprio cálculo confirmar o gabarito. "
    "Caso contrário, reprove e descreva EXATAMENTE qual critério falhou no campo 'motivo'."
)


def build_avaliador_messages(tema: str, questao: dict) -> list:
    """Monta as mensagens do Avaliador a partir do tema e da questão gerada."""
    humano = (
        f"Tema solicitado: {tema}\n\n"
        f"Questão a avaliar:\n{format_questao(questao)}\n"
        f"Gabarito informado: {questao['gabarito']}\n"
        f"Explicação informada: {questao['explicacao']}\n\n"
        "Siga os 4 passos do sistema: resolva você mesmo, compare, verifique alternativas, avalie pedagogicamente."
    )
    return [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=humano)]


def make_avaliador_node(structured_llm):
    """Devolve a função-nó do Avaliador regular."""
    def avaliador_node(state: dict, config=None) -> dict:
        msgs = build_avaliador_messages(state["tema"], state["questao"])
        avaliacao = structured_llm.invoke(msgs, config=config)
        return {
            "quality_passed": avaliacao.quality_passed,
            "motivo_rejeicao": "" if avaliacao.quality_passed else avaliacao.motivo,
        }
    return avaliador_node


def make_avaliador_final_node(structured_llm):
    """Devolve a função-nó do Avaliador final (modelo forte).
    Se rejeitar: incrementa ciclos e zera tentativas para reiniciar o ciclo.
    """
    def avaliador_final_node(state: dict, config=None) -> dict:
        msgs = build_avaliador_messages(state["tema"], state["questao"])
        avaliacao = structured_llm.invoke(msgs, config=config)
        update = {
            "quality_passed": avaliacao.quality_passed,
            "motivo_rejeicao": "" if avaliacao.quality_passed else avaliacao.motivo,
        }
        if not avaliacao.quality_passed:
            update["ciclos"] = state.get("ciclos", 0) + 1
            update["tentativas"] = 0
        return update
    return avaliador_final_node
