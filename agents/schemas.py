"""Modelos Pydantic usados na saída estruturada dos agentes."""
from typing import Literal
from pydantic import BaseModel, Field

class Questao(BaseModel):
    enunciado: str = Field(description="Enunciado completo da questão")
    resolucao: str = Field(
        description=(
            "Resolução do problema do zero, passo a passo, com os cálculos. "
            "Preencha este campo ANTES de decidir o gabarito, para garantir que a "
            "alternativa correta está de fato certa."
        )
    )
    alternativa_a: str = Field(description="Texto da alternativa A")
    alternativa_b: str = Field(description="Texto da alternativa B")
    alternativa_c: str = Field(description="Texto da alternativa C")
    alternativa_d: str = Field(description="Texto da alternativa D")
    gabarito: Literal["A", "B", "C", "D"] = Field(description="Letra da alternativa correta")
    explicacao: str = Field(description="Explicação de por que o gabarito está correto")

class Avaliacao(BaseModel):
    quality_passed: bool = Field(description="True se a questão atende a todos os critérios")
    motivo: str = Field(description="Justificativa; descreve o problema quando reprovada")

class Classificacao(BaseModel):
    codigo_bncc: str = Field(description="Código da habilidade, ex: EM13MAT302")
    descricao_habilidade: str = Field(description="Descrição da habilidade classificada")

class Resolucao(BaseModel):
    alternativa: Literal["A", "B", "C", "D"] = Field(
        description="Letra da única alternativa correta após resolver o problema"
    )

def format_questao(questao: dict) -> str:
    return (f"{questao['enunciado']}\nA) {questao['alternativa_a']}\n"
            f"B) {questao['alternativa_b']}\nC) {questao['alternativa_c']}\n"
            f"D) {questao['alternativa_d']}")
