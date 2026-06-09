from graph.state import EstadoQuestao

def test_estado_aceita_campos_esperados():
    estado: EstadoQuestao = {
        "tema": "funções do 2º grau",
        "tentativas": 0,
        "questao": {},
        "quality_passed": False,
        "motivo_rejeicao": "",
        "habilidade_bncc": "",
        "descricao_bncc": "",
    }
    assert estado["tema"] == "funções do 2º grau"
    assert estado["tentativas"] == 0
