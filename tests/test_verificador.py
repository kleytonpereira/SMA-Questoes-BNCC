from langchain_core.runnables import RunnableLambda
from agents.verificador import build_verificador_messages, make_verificador_node
from agents.schemas import Resolucao

QUESTAO = {
    "enunciado": "Quanto é 2+2?",
    "alternativa_a": "3", "alternativa_b": "4",
    "alternativa_c": "5", "alternativa_d": "6",
    "gabarito": "B", "explicacao": "2+2=4.",
}

def test_build_messages_inclui_alternativas_mas_nao_gabarito():
    msgs = build_verificador_messages(QUESTAO)
    conteudo = " ".join(m.content for m in msgs)
    assert "Quanto é 2+2?" in conteudo
    assert "B) 4" in conteudo
    # Não deve revelar qual é o gabarito
    assert "gabarito" not in conteudo.lower()

def test_maioria_concorda_com_gabarito_aprova():
    fake = RunnableLambda(lambda _: Resolucao(alternativa="B"))
    node = make_verificador_node(fake, n_samples=3)
    update = node({"questao": QUESTAO})
    assert update["quality_passed"] is True
    assert update["motivo_rejeicao"] == ""

def test_maioria_diverge_do_gabarito_reprova():
    fake = RunnableLambda(lambda _: Resolucao(alternativa="C"))
    node = make_verificador_node(fake, n_samples=3)
    update = node({"questao": QUESTAO})
    assert update["quality_passed"] is False
    assert "C" in update["motivo_rejeicao"]
    assert "B" in update["motivo_rejeicao"]

def test_voto_majoritario_com_empate_parcial():
    # Sequência B, C, B -> maioria B (concorda com gabarito)
    respostas = iter(["B", "C", "B"])
    fake = RunnableLambda(lambda _: Resolucao(alternativa=next(respostas)))
    node = make_verificador_node(fake, n_samples=3)
    update = node({"questao": QUESTAO})
    assert update["quality_passed"] is True
