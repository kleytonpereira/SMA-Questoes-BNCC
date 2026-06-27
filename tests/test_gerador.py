from langchain_core.runnables import RunnableLambda
from agents.gerador import build_gerador_messages, make_gerador_node
from agents.schemas import Questao

def questao_fake() -> Questao:
    return Questao(
        enunciado="Qual o vértice de y=x²?",
        resolucao="y=x² tem a=1, b=0, c=0; x do vértice = -b/2a = 0; y(0)=0.",
        alternativa_a="(0,0)", alternativa_b="(1,1)",
        alternativa_c="(0,1)", alternativa_d="(1,0)",
        gabarito="A", explicacao="O vértice de y=x² é a origem.",
    )

def test_build_messages_primeira_tentativa_inclui_tema_sem_rejeicao():
    msgs = build_gerador_messages("funções do 2º grau", "")
    conteudo = " ".join(m.content for m in msgs)
    assert "funções do 2º grau" in conteudo
    assert "REJEITADA" not in conteudo

def test_build_messages_retry_inclui_motivo_rejeicao():
    msgs = build_gerador_messages("funções", "Alternativa C incorreta")
    conteudo = " ".join(m.content for m in msgs)
    assert "Alternativa C incorreta" in conteudo
    assert "REJEITADA" in conteudo

def test_gerador_node_incrementa_tentativas_e_salva_questao():
    fake_llm = RunnableLambda(lambda _: questao_fake())
    node = make_gerador_node(fake_llm)
    update = node({"tema": "funções", "tentativas": 0, "motivo_rejeicao": ""})
    assert update["tentativas"] == 1
    assert update["questao"]["gabarito"] == "A"
    assert update["questao"]["enunciado"] == "Qual o vértice de y=x²?"

def test_gerador_node_incrementa_a_partir_do_valor_atual():
    fake_llm = RunnableLambda(lambda _: questao_fake())
    node = make_gerador_node(fake_llm)
    update = node({"tema": "funções", "tentativas": 1, "motivo_rejeicao": "erro"})
    assert update["tentativas"] == 2
