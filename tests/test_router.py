from graph.router import decide_apos_avaliador, decide_apos_avaliador_final


# --- decide_apos_avaliador ---

def test_aprovada_vai_para_avaliador_final():
    assert decide_apos_avaliador({"quality_passed": True, "tentativas": 1}) == "avaliador_final"

def test_aprovada_sempre_passa_pelo_avaliador_final():
    assert decide_apos_avaliador({"quality_passed": True, "tentativas": 3}) == "avaliador_final"

def test_reprovada_com_tentativas_restantes_volta_para_gerador():
    assert decide_apos_avaliador({"quality_passed": False, "tentativas": 1}) == "gerador"
    assert decide_apos_avaliador({"quality_passed": False, "tentativas": 2}) == "gerador"

def test_reprovada_no_limite_vai_para_avaliador_final():
    assert decide_apos_avaliador({"quality_passed": False, "tentativas": 3}) == "avaliador_final"


# --- decide_apos_avaliador_final ---

def test_final_aprovada_vai_para_organizador():
    assert decide_apos_avaliador_final({"quality_passed": True, "ciclos": 1}) == "organizador"

def test_final_reprovada_com_ciclos_disponiveis_volta_para_gerador():
    assert decide_apos_avaliador_final({"quality_passed": False, "ciclos": 0}) == "gerador"
    assert decide_apos_avaliador_final({"quality_passed": False, "ciclos": 1}) == "gerador"

def test_final_reprovada_ciclos_esgotados_vai_para_organizador():
    assert decide_apos_avaliador_final({"quality_passed": False, "ciclos": 2}) == "organizador"

def test_final_sem_campo_ciclos_usa_zero():
    assert decide_apos_avaliador_final({"quality_passed": False}) == "gerador"
