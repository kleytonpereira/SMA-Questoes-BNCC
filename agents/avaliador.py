"""Agente Avaliador: aprova ou rejeita a questão gerada."""
from langchain_core.messages import SystemMessage, HumanMessage
from agents.schemas import format_questao

SYSTEM_PROMPT = (
    "Você é um revisor pedagógico rigoroso de questões de Matemática do Ensino "
    "Médio. Avalie a questão segundo os critérios:\n"
    "1. O gabarito está matematicamente correto e é a ÚNICA alternativa correta.\n"
    "2. As alternativas erradas são plausíveis e não óbvias.\n"
    "3. A linguagem é adequada ao Ensino Médio.\n"
    "4. A questão corresponde ao tema solicitado.\n"
    "5. O enunciado não é ambíguo.\n"
    "Se TODOS os critérios forem atendidos, aprove (quality_passed=true). Caso "
    "contrário, reprove (quality_passed=false) e descreva objetivamente o "
    "problema principal no campo 'motivo'."
)

def build_avaliador_messages(tema: str, questao: dict) -> list:
    humano = (
        f"Tema solicitado: {tema}\n\n"
        f"Questão a avaliar:\n{format_questao(questao)}\n"
        f"Gabarito informado: {questao['gabarito']}\n"
        f"Explicação informada: {questao['explicacao']}"
    )
    return [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=humano)]

def make_avaliador_node(structured_llm):
    def avaliador_node(state: dict) -> dict:
        msgs = build_avaliador_messages(state["tema"], state["questao"])
        avaliacao = structured_llm.invoke(msgs)
        return {
            "quality_passed": avaliacao.quality_passed,
            "motivo_rejeicao": "" if avaliacao.quality_passed else avaliacao.motivo,
        }
    return avaliador_node
