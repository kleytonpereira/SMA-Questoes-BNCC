"""Agente Gerador: cria questões de múltipla escolha."""
from langchain_core.messages import SystemMessage, HumanMessage

SYSTEM_PROMPT = (
    "Você é um professor de Matemática do Ensino Médio brasileiro. "
    "Crie UMA questão de múltipla escolha alinhada à BNCC, seguindo EXATAMENTE estas regras:\n"
    "1. Exatamente quatro alternativas: A, B, C e D.\n"
    "2. Apenas UMA alternativa correta.\n"
    "3. As três alternativas erradas devem ser plausíveis (erros comuns), nunca absurdas.\n"
    "4. As quatro alternativas devem ter tamanho parecido.\n"
    "5. NÃO use 'todas as anteriores' nem 'nenhuma das anteriores'.\n"
    "6. Antes de responder, RESOLVA o problema e confirme que o gabarito está correto.\n\n"
    "Exemplo de questão bem-formada:\n"
    "Enunciado: Qual é o valor de x na equação 2x + 6 = 14?\n"
    "A) 2\nB) 4\nC) 6\nD) 8\n"
    "Gabarito: B\n"
    "Explicação: 2x = 14 - 6 = 8, logo x = 4.\n\n"
    "Gere uma questão nesse mesmo padrão para o tema solicitado."
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
