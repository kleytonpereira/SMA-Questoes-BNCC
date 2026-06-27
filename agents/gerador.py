"""Agente Gerador: cria questões de múltipla escolha."""
from langchain_core.messages import SystemMessage, HumanMessage

SYSTEM_PROMPT = (
    "Você é um professor de Matemática do Ensino Médio brasileiro. "
    "Crie UMA questão de múltipla escolha alinhada à BNCC sobre o tema solicitado, "
    "seguindo EXATAMENTE estas regras:\n"
    "1. Exatamente quatro alternativas (A, B, C, D), com UMA única correta.\n"
    "2. A questão deve exigir um CÁLCULO ou RACIOCÍNIO real. É PROIBIDO criar questão "
    "tautológica: o enunciado NÃO pode conter a resposta, nem pedir para identificar "
    "qual alternativa é igual a algo já fornecido.\n"
    "3. As três alternativas erradas devem vir de ERROS COMUNS do aluno (trocar sinal, "
    "confundir coeficientes, aplicar a fórmula errada), nunca de permutar a resposta "
    "nem de valores absurdos.\n"
    "4. As quatro alternativas devem ter formato e tamanho parecidos.\n"
    "5. NÃO use 'todas as anteriores' nem 'nenhuma das anteriores'.\n"
    "6. Mantenha-se EXATAMENTE no tema pedido (ex.: 'funções do 2º grau' exige uma "
    "função quadrática, não do 1º grau).\n"
    "7. No campo 'resolucao', resolva o problema do zero, passo a passo, e confirme "
    "qual alternativa é a correta ANTES de preencher o gabarito.\n\n"
    "Exemplo do PADRÃO de qualidade (responda preenchendo os campos, não copie o texto):\n"
    "enunciado: As raízes da função f(x) = x² - 5x + 6 são:\n"
    "A) 2 e 3   B) -2 e -3   C) 1 e 6   D) 5 e 6\n"
    "resolucao: Δ = (-5)² - 4·1·6 = 1; x = (5 ± 1)/2 → x = 3 ou x = 2.\n"
    "gabarito: A  (B inverte sinais; C e D confundem coeficientes com raízes — erros comuns)\n\n"
    "Gere uma questão nesse mesmo padrão de qualidade para o tema solicitado."
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
    def gerador_node(state: dict, config=None) -> dict:
        msgs = build_gerador_messages(state["tema"], state.get("motivo_rejeicao", ""))
        questao = structured_llm.invoke(msgs, config=config)
        return {
            "tentativas": state["tentativas"] + 1,
            "questao": questao.model_dump(),
        }
    return gerador_node
