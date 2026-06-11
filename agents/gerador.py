"""Agente Gerador: cria questões de múltipla escolha."""
from langchain_core.messages import SystemMessage, HumanMessage

SYSTEM_PROMPT = (
    "Você é um professor especialista em Matemática do Ensino Médio brasileiro. "
    "Sua tarefa é criar UMA questão de múltipla escolha alinhada à BNCC, com "
    "exatamente quatro alternativas (A, B, C e D), das quais apenas UMA é correta. "
    "As alternativas incorretas devem ser plausíveis (erros comuns dos alunos), "
    "nunca absurdas. Use linguagem adequada ao Ensino Médio e forneça uma "
    "explicação clara do gabarito."
)

def build_gerador_messages(tema: str, motivo_rejeicao: str) -> list:
    humano = f"Tema solicitado: {tema}\n\nGere a questão."
    if motivo_rejeicao:
        humano += (
            "\n\nATENÇÃO: a tentativa anterior foi REJEITADA pelo revisor com a "
            f'seguinte justificativa:\n"{motivo_rejeicao}"\n'
            "Corrija especificamente esse problema na nova questão."
        )
    return [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=humano)]

def make_gerador_node(structured_llm):
    def gerador_node(state: dict) -> dict:
        msgs = build_gerador_messages(state["tema"], state.get("motivo_rejeicao", ""))
        questao = structured_llm.invoke(msgs)
        return {
            "tentativas": state["tentativas"] + 1,
            "questao": questao.model_dump(),
        }
    return gerador_node
