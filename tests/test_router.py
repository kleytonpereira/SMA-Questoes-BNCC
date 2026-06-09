from graph.router import decide_proximo

def test_aprovada_vai_para_organizador():
    assert decide_proximo({"quality_passed": True, "tentativas": 1}) == "organizador"

def test_reprovada_com_tentativas_restantes_volta_para_gerador():
    assert decide_proximo({"quality_passed": False, "tentativas": 1}) == "gerador"
    assert decide_proximo({"quality_passed": False, "tentativas": 2}) == "gerador"

def test_reprovada_no_limite_vai_para_organizador():
    assert decide_proximo({"quality_passed": False, "tentativas": 3}) == "organizador"

def test_aprovada_tem_prioridade_sobre_limite():
    assert decide_proximo({"quality_passed": True, "tentativas": 3}) == "organizador"
