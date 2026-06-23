from graph.workflow import build_workflow

BASE_STATE = {
    "tema": "funções",
    "tentativas": 0,
    "ciclos": 0,
    "regras_passed": False,
    "quality_passed": False,
    "motivo_rejeicao": "",
    "questao": {},
    "habilidade_bncc": "",
    "descricao_bncc": "",
}


def _make_app(gerador, validador, verificador, avaliador, avaliador_final, organizador):
    return build_workflow(gerador, validador, verificador, avaliador, avaliador_final, organizador)


def test_workflow_fluxo_feliz_passa_por_todas_as_camadas():
    ordem = []

    def gerador(state):
        ordem.append("gerador")
        return {"tentativas": state["tentativas"] + 1, "questao": {"gabarito": "A"}}
    def validador(state):
        ordem.append("validador")
        return {"regras_passed": True, "motivo_rejeicao": ""}
    def verificador(state):
        ordem.append("verificador")
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def avaliador(state):
        ordem.append("avaliador")
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def avaliador_final(state):
        ordem.append("avaliador_final")
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def organizador(state):
        ordem.append("organizador")
        return {"habilidade_bncc": "EM13MAT302", "descricao_bncc": "Funções"}

    app = _make_app(gerador, validador, verificador, avaliador, avaliador_final, organizador)
    final = app.invoke(BASE_STATE)
    assert ordem == ["gerador", "validador", "verificador", "avaliador", "avaliador_final", "organizador"]
    assert final["habilidade_bncc"] == "EM13MAT302"


def test_workflow_regras_falham_voltam_ao_gerador():
    chamadas = {"validador": 0}

    def gerador(state):
        return {"tentativas": state["tentativas"] + 1, "questao": {"gabarito": "A"}}
    def validador(state):
        chamadas["validador"] += 1
        if chamadas["validador"] == 1:
            return {"regras_passed": False, "motivo_rejeicao": "Alternativa vazia"}
        return {"regras_passed": True, "motivo_rejeicao": ""}
    def verificador(state):
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def avaliador(state):
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def avaliador_final(state):
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def organizador(state):
        return {"habilidade_bncc": "EM13MAT302", "descricao_bncc": "Funções"}

    app = _make_app(gerador, validador, verificador, avaliador, avaliador_final, organizador)
    final = app.invoke(BASE_STATE)
    assert chamadas["validador"] == 2
    assert final["tentativas"] == 2


def test_workflow_verificador_diverge_volta_ao_gerador():
    chamadas = {"verificador": 0}

    def gerador(state):
        return {"tentativas": state["tentativas"] + 1, "questao": {"gabarito": "A"}}
    def validador(state):
        return {"regras_passed": True, "motivo_rejeicao": ""}
    def verificador(state):
        chamadas["verificador"] += 1
        if chamadas["verificador"] == 1:
            return {"quality_passed": False, "motivo_rejeicao": "Divergência"}
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def avaliador(state):
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def avaliador_final(state):
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def organizador(state):
        return {"habilidade_bncc": "EM13MAT302", "descricao_bncc": "Funções"}

    app = _make_app(gerador, validador, verificador, avaliador, avaliador_final, organizador)
    final = app.invoke(BASE_STATE)
    assert chamadas["verificador"] == 2
    assert final["habilidade_bncc"] == "EM13MAT302"


def test_workflow_avaliador_aprovado_passa_pelo_avaliador_final():
    chamadas = {"avaliador_final": 0}

    def gerador(state):
        return {"tentativas": state["tentativas"] + 1, "questao": {"gabarito": "A"}}
    def validador(state):
        return {"regras_passed": True, "motivo_rejeicao": ""}
    def verificador(state):
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def avaliador(state):
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def avaliador_final(state):
        chamadas["avaliador_final"] += 1
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def organizador(state):
        return {"habilidade_bncc": "EM13MAT302", "descricao_bncc": "Funções"}

    app = _make_app(gerador, validador, verificador, avaliador, avaliador_final, organizador)
    final = app.invoke(BASE_STATE)
    assert chamadas["avaliador_final"] == 1
    assert final["quality_passed"] is True
