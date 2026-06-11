from bncc.loader import load_habilidades, format_habilidades

def test_load_habilidades_retorna_lista_com_codigo_e_descricao():
    habilidades = load_habilidades("data/bncc_matematica.json")
    assert isinstance(habilidades, list)
    assert len(habilidades) >= 10
    primeira = habilidades[0]
    assert "codigo" in primeira
    assert "descricao" in primeira
    assert primeira["codigo"].startswith("EM13MAT")

def test_format_habilidades_gera_linhas_codigo_descricao():
    habilidades = [
        {"codigo": "EM13MAT302", "descricao": "Funções polinomiais de 1º ou 2º graus."},
        {"codigo": "EM13MAT507", "descricao": "Probabilidade."},
    ]
    texto = format_habilidades(habilidades)
    assert "EM13MAT302: Funções polinomiais de 1º ou 2º graus." in texto
    assert "EM13MAT507: Probabilidade." in texto
    assert texto.count("\n") == 1
