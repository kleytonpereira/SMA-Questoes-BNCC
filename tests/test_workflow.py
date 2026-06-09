from graph.workflow import build_workflow

def test_workflow_fluxo_feliz_aprovado_na_primeira():
    def gerador(state):
        return {"tentativas": state["tentativas"] + 1, "questao": {"gabarito": "A"}}
    def avaliador(state):
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def organizador(state):
        return {"habilidade_bncc": "EM13MAT302", "descricao_bncc": "Funções"}

    app = build_workflow(gerador, avaliador, organizador)
    final = app.invoke(
        {"tema": "funções", "tentativas": 0, "quality_passed": False, "motivo_rejeicao": ""}
    )
    assert final["tentativas"] == 1
    assert final["quality_passed"] is True
    assert final["habilidade_bncc"] == "EM13MAT302"

def test_workflow_loop_rejeita_uma_vez_depois_aprova():
    chamadas = {"avaliador": 0}

    def gerador(state):
        return {"tentativas": state["tentativas"] + 1, "questao": {"gabarito": "A"}}

    def avaliador(state):
        chamadas["avaliador"] += 1
        if chamadas["avaliador"] == 1:
            return {"quality_passed": False, "motivo_rejeicao": "Gabarito errado"}
        return {"quality_passed": True, "motivo_rejeicao": ""}

    def organizador(state):
        return {"habilidade_bncc": "EM13MAT302", "descricao_bncc": "Funções"}

    app = build_workflow(gerador, avaliador, organizador)
    final = app.invoke(
        {"tema": "funções", "tentativas": 0, "quality_passed": False, "motivo_rejeicao": ""}
    )
    assert chamadas["avaliador"] == 2
    assert final["tentativas"] == 2
    assert final["quality_passed"] is True

def test_workflow_para_no_limite_de_tentativas_sem_aprovacao():
    def gerador(state):
        return {"tentativas": state["tentativas"] + 1, "questao": {"gabarito": "A"}}
    def avaliador(state):
        return {"quality_passed": False, "motivo_rejeicao": "Sempre ruim"}
    def organizador(state):
        return {"habilidade_bncc": "EM13MAT302", "descricao_bncc": "Funções"}

    app = build_workflow(gerador, avaliador, organizador)
    final = app.invoke(
        {"tema": "funções", "tentativas": 0, "quality_passed": False, "motivo_rejeicao": ""}
    )
    assert final["tentativas"] == 3
    assert final["quality_passed"] is False
    assert final["habilidade_bncc"] == "EM13MAT302"
