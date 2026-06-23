"""Roteadores do quality gate: decidem para onde o fluxo vai após avaliações."""
from typing import Literal
import config


def decide_apos_avaliador(state: dict) -> Literal["gerador", "avaliador_final"]:
    """Após avaliador regular:
    - Aprovada → avaliador_final (segunda opinião)
    - Reprovada e tentativas esgotadas → avaliador_final (último recurso)
    - Reprovada e ainda há tentativas → gerador (tenta de novo)
    """
    if state["quality_passed"] or state["tentativas"] >= config.MAX_TENTATIVAS:
        return "avaliador_final"
    return "gerador"


def decide_apos_avaliador_final(state: dict) -> Literal["gerador", "organizador"]:
    """Após avaliador final (modelo forte):
    - Aprovada → organizador
    - Reprovada e ciclos disponíveis → gerador (reinicia ciclo com modelo menor)
    - Reprovada e ciclos esgotados → organizador (entrega com aviso)
    """
    if state["quality_passed"]:
        return "organizador"
    if state.get("ciclos", 0) < config.MAX_CICLOS:
        return "gerador"
    return "organizador"


def decide_apos_validador(state: dict) -> Literal["gerador", "verificador"]:
    """Após o validador de regras:
    - Regras OK → verificador
    - Regras falharam e ainda há tentativas → gerador
    - Regras falharam e tentativas esgotadas → verificador (camadas seguintes julgam)
    """
    if state.get("regras_passed"):
        return "verificador"
    if state["tentativas"] >= config.MAX_TENTATIVAS:
        return "verificador"
    return "gerador"


def decide_apos_verificador(state: dict) -> Literal["gerador", "avaliador"]:
    """Após o verificador (auto-consistência):
    - Aprovado → avaliador
    - Reprovado e ainda há tentativas → gerador
    - Reprovado e tentativas esgotadas → avaliador
    """
    if state["quality_passed"]:
        return "avaliador"
    if state["tentativas"] >= config.MAX_TENTATIVAS:
        return "avaliador"
    return "gerador"
