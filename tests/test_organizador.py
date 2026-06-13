from langchain_core.runnables import RunnableLambda
from agents.organizador import build_organizador_messages, make_organizador_node
from agents.schemas import Classificacao

QUESTAO = {
    "enunciado": "Qual o vértice de y=x²?",
    "alternativa_a": "(0,0)", "alternativa_b": "(1,1)",
    "alternativa_c": "(0,1)", "alternativa_d": "(1,0)",
    "gabarito": "A", "explicacao": "O vértice de y=x² é a origem.",
}
HABILIDADES_TEXTO = (
    "EM13MAT302: Funções polinomiais de 1º ou 2º graus.\n"
    "EM13MAT507: Probabilidade."
)

def test_build_messages_inclui_habilidades_e_questao():
    msgs = build_organizador_messages(QUESTAO, HABILIDADES_TEXTO)
    conteudo = " ".join(m.content for m in msgs)
    assert "EM13MAT302" in conteudo
    assert "Qual o vértice de y=x²?" in conteudo

def test_organizador_node_salva_codigo_e_descricao():
    fake_llm = RunnableLambda(lambda _: Classificacao(codigo_bncc="EM13MAT302", descricao_habilidade="Funções"))
    node = make_organizador_node(fake_llm, HABILIDADES_TEXTO)
    update = node({"questao": QUESTAO})
    assert update["habilidade_bncc"] == "EM13MAT302"
    assert update["descricao_bncc"] == "Funções"
