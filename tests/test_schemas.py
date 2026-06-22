import pytest
from pydantic import ValidationError
from agents.schemas import Questao, Avaliacao, Classificacao, format_questao


def make_questao(**kw):
    base = dict(
        enunciado="Qual o valor de 2+2?",
        alternativa_a="3",
        alternativa_b="4",
        alternativa_c="5",
        alternativa_d="6",
        gabarito="B",
        explicacao="2+2=4",
    )
    base.update(kw)
    return base


def test_questao_valida():
    q = Questao(**make_questao())
    assert q.gabarito == "B"
    assert q.alternativa_b == "4"


def test_questao_gabarito_invalido_levanta_erro():
    with pytest.raises(ValidationError):
        Questao(**make_questao(gabarito="E"))


def test_avaliacao_valida():
    a = Avaliacao(quality_passed=False, motivo="Gabarito incorreto")
    assert a.quality_passed is False
    assert "incorreto" in a.motivo


def test_classificacao_valida():
    c = Classificacao(codigo_bncc="EM13MAT302", descricao_habilidade="Funções quadráticas")
    assert c.codigo_bncc == "EM13MAT302"


def test_format_questao_inclui_enunciado_e_alternativas():
    texto = format_questao(make_questao())
    assert "Qual o valor de 2+2?" in texto
    assert "A) 3" in texto
    assert "B) 4" in texto
    assert "C) 5" in texto
    assert "D) 6" in texto


def test_resolucao_valida():
    from agents.schemas import Resolucao
    r = Resolucao(alternativa="B")
    assert r.alternativa == "B"


def test_resolucao_rejeita_letra_invalida():
    import pytest
    from pydantic import ValidationError
    from agents.schemas import Resolucao
    with pytest.raises(ValidationError):
        Resolucao(alternativa="Z")
