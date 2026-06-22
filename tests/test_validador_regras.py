from agents.validador_regras import validar_regras, make_validador_regras_node

QUESTAO_OK = {
    "enunciado": "Qual o valor de 2+2?",
    "alternativa_a": "3", "alternativa_b": "4",
    "alternativa_c": "5", "alternativa_d": "6",
    "gabarito": "B", "explicacao": "2+2=4.",
}

def test_questao_valida_passa():
    passou, motivo = validar_regras(QUESTAO_OK)
    assert passou is True
    assert motivo == ""

def test_gabarito_invalido_reprova():
    q = {**QUESTAO_OK, "gabarito": "Z"}
    passou, motivo = validar_regras(q)
    assert passou is False
    assert "Gabarito" in motivo

def test_alternativa_vazia_reprova():
    q = {**QUESTAO_OK, "alternativa_c": "   "}
    passou, motivo = validar_regras(q)
    assert passou is False
    assert "vazia" in motivo.lower()

def test_alternativas_duplicadas_reprova():
    q = {**QUESTAO_OK, "alternativa_a": "4"}  # igual à B
    passou, motivo = validar_regras(q)
    assert passou is False
    assert "duplicad" in motivo.lower()

def test_todas_as_anteriores_reprova():
    q = {**QUESTAO_OK, "alternativa_d": "Todas as anteriores"}
    passou, motivo = validar_regras(q)
    assert passou is False
    assert "anteriores" in motivo.lower()

def test_correta_muito_mais_longa_reprova():
    q = {
        "enunciado": "Pergunta?",
        "alternativa_a": "x", "alternativa_b": "y",
        "alternativa_c": "Esta alternativa correta é deliberadamente muito mais longa que as outras todas",
        "alternativa_d": "z",
        "gabarito": "C", "explicacao": "...",
    }
    passou, motivo = validar_regras(q)
    assert passou is False
    assert "longa" in motivo.lower()

def test_termos_absolutos_desligado_por_padrao():
    q = {**QUESTAO_OK, "enunciado": "O resultado é sempre 4?"}
    passou, _ = validar_regras(q)
    assert passou is True

def test_termos_absolutos_ligado_reprova():
    q = {**QUESTAO_OK, "enunciado": "O resultado é sempre 4?"}
    passou, motivo = validar_regras(q, checar_termos_absolutos=True)
    assert passou is False
    assert "absoluto" in motivo.lower()

def test_node_seta_regras_passed_true():
    node = make_validador_regras_node()
    update = node({"questao": QUESTAO_OK})
    assert update["regras_passed"] is True
    assert update["motivo_rejeicao"] == ""

def test_node_seta_regras_passed_false_com_motivo():
    node = make_validador_regras_node()
    q = {**QUESTAO_OK, "gabarito": "Z"}
    update = node({"questao": q})
    assert update["regras_passed"] is False
    assert update["motivo_rejeicao"] != ""
