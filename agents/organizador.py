"""Agente Organizador: classifica a questão segundo a BNCC."""
from langchain_core.messages import SystemMessage, HumanMessage
from agents.schemas import format_questao

SYSTEM_PROMPT = (
    "Você classifica questões de Matemática do Ensino Médio segundo as "
    "habilidades da BNCC. Escolha o ÚNICO código de habilidade mais adequado ao "
    "conteúdo da questão, dentre a lista fornecida. Retorne o código exatamente "
    "como aparece na lista e a descrição correspondente."
)

def build_organizador_messages(questao: dict, habilidades_texto: str) -> list:
    humano = (
        f"Habilidades disponíveis:\n{habilidades_texto}\n\n"
        f"Questão a classificar:\n{format_questao(questao)}\n\n"
        "Classifique escolhendo o código mais adequado."
    )
    return [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=humano)]

def make_organizador_node(structured_llm, habilidades_texto: str):
    def organizador_node(state: dict) -> dict:
        msgs = build_organizador_messages(state["questao"], habilidades_texto)
        classificacao = structured_llm.invoke(msgs)
        return {
            "habilidade_bncc": classificacao.codigo_bncc,
            "descricao_bncc": classificacao.descricao_habilidade,
        }
    return organizador_node
