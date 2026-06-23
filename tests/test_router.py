from graph.router import decide_apos_avaliador, decide_apos_avaliador_final, decide_apos_validador, decide_apos_verificador


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


# --- decide_apos_validador ---

def test_validador_regras_ok_vai_para_verificador():
    assert decide_apos_validador({"regras_passed": True, "tentativas": 1}) == "verificador"

def test_validador_regras_falha_com_tentativas_volta_para_gerador():
    assert decide_apos_validador({"regras_passed": False, "tentativas": 1}) == "gerador"

def test_validador_regras_falha_no_limite_segue_para_verificador():
    assert decide_apos_validador({"regras_passed": False, "tentativas": 3}) == "verificador"

# --- decide_apos_verificador ---

def test_verificador_aprovado_vai_para_avaliador():
    assert decide_apos_verificador({"quality_passed": True, "tentativas": 1}) == "avaliador"

def test_verificador_reprovado_com_tentativas_volta_para_gerador():
    assert decide_apos_verificador({"quality_passed": False, "tentativas": 1}) == "gerador"

def test_verificador_reprovado_no_limite_segue_para_avaliador():
    assert decide_apos_verificador({"quality_passed": False, "tentativas": 3}) == "avaliador"
