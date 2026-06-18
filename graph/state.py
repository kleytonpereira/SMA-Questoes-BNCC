"""Estado compartilhado entre os nós do grafo LangGraph."""
from typing import TypedDict

class EstadoQuestao(TypedDict):
    tema: str
    tentativas: int
    ciclos: int
    questao: dict
    quality_passed: bool
    motivo_rejeicao: str
    habilidade_bncc: str
    descricao_bncc: str
