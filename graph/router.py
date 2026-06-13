"""Roteador do quality gate: decide regerar ou seguir para classificação."""
from typing import Literal
import config

def decide_proximo(state: dict) -> Literal["gerador", "organizador"]:
    """Decide o próximo nó após a avaliação.
    - Aprovada -> organizador.
    - Reprovada e ainda há tentativas (< MAX_TENTATIVAS) -> gerador.
    - Reprovada e atingiu o limite -> organizador (entrega com aviso).
    """
    if state["quality_passed"]:
        return "organizador"
    if state["tentativas"] >= config.MAX_TENTATIVAS:
        return "organizador"
    return "gerador"
