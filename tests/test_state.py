from graph.state import EstadoQuestao

def test_estado_aceita_campos_esperados():
    from graph.state import EstadoQuestao
    estado: EstadoQuestao = {
        "tema": "funções",
        "tentativas": 0,
        "ciclos": 0,
        "regras_passed": False,
        "questao": {},
        "quality_passed": False,
        "motivo_rejeicao": "",
        "habilidade_bncc": "",
        "descricao_bncc": "",
    }
    assert estado["regras_passed"] is False
    assert estado["tema"] == "funções"
