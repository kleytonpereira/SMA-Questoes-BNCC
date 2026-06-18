from langchain_core.runnables import RunnableLambda
from agents.avaliador import build_avaliador_messages, make_avaliador_node, make_avaliador_final_node
from agents.schemas import Avaliacao

QUESTAO = {
    "enunciado": "Qual o vértice de y=x²?",
    "alternativa_a": "(0,0)", "alternativa_b": "(1,1)",
    "alternativa_c": "(0,1)", "alternativa_d": "(1,0)",
    "gabarito": "A", "explicacao": "O vértice de y=x² é a origem.",
}

def test_build_messages_inclui_tema_e_questao():
    msgs = build_avaliador_messages("funções do 2º grau", QUESTAO)
    conteudo = " ".join(m.content for m in msgs)
    assert "funções do 2º grau" in conteudo
    assert "Qual o vértice de y=x²?" in conteudo
    assert "A) (0,0)" in conteudo

def test_avaliador_node_aprovada_define_quality_passed_true_e_limpa_motivo():
    fake_llm = RunnableLambda(lambda _: Avaliacao(quality_passed=True, motivo="Aprovada"))
    node = make_avaliador_node(fake_llm)
    update = node({"tema": "funções", "questao": QUESTAO})
    assert update["quality_passed"] is True
    assert update["motivo_rejeicao"] == ""

def test_avaliador_node_reprovada_propaga_motivo():
    fake_llm = RunnableLambda(lambda _: Avaliacao(quality_passed=False, motivo="Gabarito incorreto"))
    node = make_avaliador_node(fake_llm)
    update = node({"tema": "funções", "questao": QUESTAO})
    assert update["quality_passed"] is False
    assert update["motivo_rejeicao"] == "Gabarito incorreto"


# --- avaliador_final ---

def test_avaliador_final_aprovada_nao_altera_ciclos():
    fake_llm = RunnableLambda(lambda _: Avaliacao(quality_passed=True, motivo="OK"))
    node = make_avaliador_final_node(fake_llm)
    update = node({"tema": "funções", "questao": QUESTAO, "ciclos": 0, "tentativas": 3})
    assert update["quality_passed"] is True
    assert "ciclos" not in update

def test_avaliador_final_reprovada_incrementa_ciclos_e_zera_tentativas():
    fake_llm = RunnableLambda(lambda _: Avaliacao(quality_passed=False, motivo="Gabarito errado"))
    node = make_avaliador_final_node(fake_llm)
    update = node({"tema": "funções", "questao": QUESTAO, "ciclos": 0, "tentativas": 3})
    assert update["quality_passed"] is False
    assert update["ciclos"] == 1
    assert update["tentativas"] == 0

def test_avaliador_final_reprovada_acumula_ciclos():
    fake_llm = RunnableLambda(lambda _: Avaliacao(quality_passed=False, motivo="Erro"))
    node = make_avaliador_final_node(fake_llm)
    update = node({"tema": "funções", "questao": QUESTAO, "ciclos": 1, "tentativas": 3})
    assert update["ciclos"] == 2
