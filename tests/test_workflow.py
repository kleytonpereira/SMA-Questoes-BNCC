from graph.workflow import build_workflow

BASE_STATE = {
    "tema": "funções",
    "tentativas": 0,
    "ciclos": 0,
    "quality_passed": False,
    "motivo_rejeicao": "",
    "questao": {},
    "habilidade_bncc": "",
    "descricao_bncc": "",
}


def _make_app(gerador, avaliador, avaliador_final, organizador):
    return build_workflow(gerador, avaliador, avaliador_final, organizador)


def test_workflow_fluxo_feliz_aprovado_na_primeira():
    def gerador(state):
        return {"tentativas": state["tentativas"] + 1, "questao": {"gabarito": "A"}}
    def avaliador(state):
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def avaliador_final(state):
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def organizador(state):
        return {"habilidade_bncc": "EM13MAT302", "descricao_bncc": "Funções"}

    app = _make_app(gerador, avaliador, avaliador_final, organizador)
    final = app.invoke(BASE_STATE)
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

    def avaliador_final(state):
        return {"quality_passed": True, "motivo_rejeicao": ""}

    def organizador(state):
        return {"habilidade_bncc": "EM13MAT302", "descricao_bncc": "Funções"}

    app = _make_app(gerador, avaliador, avaliador_final, organizador)
    final = app.invoke(BASE_STATE)
    assert chamadas["avaliador"] == 2
    assert final["tentativas"] == 2
    assert final["quality_passed"] is True


def test_workflow_aprovada_sempre_passa_pelo_avaliador_final():
    chamadas = {"avaliador_final": 0}

    def gerador(state):
        return {"tentativas": state["tentativas"] + 1, "questao": {"gabarito": "A"}}

    def avaliador(state):
        return {"quality_passed": True, "motivo_rejeicao": ""}

    def avaliador_final(state):
        chamadas["avaliador_final"] += 1
        return {"quality_passed": True, "motivo_rejeicao": ""}

    def organizador(state):
        return {"habilidade_bncc": "EM13MAT302", "descricao_bncc": "Funções"}

    app = _make_app(gerador, avaliador, avaliador_final, organizador)
    final = app.invoke(BASE_STATE)
    assert chamadas["avaliador_final"] == 1
    assert final["quality_passed"] is True

def test_workflow_esgota_tentativas_aciona_avaliador_final():
    chamadas = {"avaliador_final": 0}

    def gerador(state):
        return {"tentativas": state["tentativas"] + 1, "questao": {"gabarito": "A"}}

    def avaliador(state):
        return {"quality_passed": False, "motivo_rejeicao": "Sempre ruim"}

    def avaliador_final(state):
        chamadas["avaliador_final"] += 1
        return {"quality_passed": True, "motivo_rejeicao": ""}

    def organizador(state):
        return {"habilidade_bncc": "EM13MAT302", "descricao_bncc": "Funções"}

    app = _make_app(gerador, avaliador, avaliador_final, organizador)
    final = app.invoke(BASE_STATE)
    assert chamadas["avaliador_final"] == 1
    assert final["quality_passed"] is True


def test_workflow_para_no_limite_de_ciclos_sem_aprovacao():
    def gerador(state):
        return {"tentativas": state["tentativas"] + 1, "questao": {"gabarito": "A"}}

    def avaliador(state):
        return {"quality_passed": False, "motivo_rejeicao": "Sempre ruim"}

    def avaliador_final(state):
        ciclos = state.get("ciclos", 0) + 1
        return {"quality_passed": False, "motivo_rejeicao": "Ainda ruim", "ciclos": ciclos, "tentativas": 0}

    def organizador(state):
        return {"habilidade_bncc": "EM13MAT302", "descricao_bncc": "Funções"}

    app = _make_app(gerador, avaliador, avaliador_final, organizador)
    final = app.invoke(BASE_STATE)
    assert final["quality_passed"] is False
    assert final["habilidade_bncc"] == "EM13MAT302"
