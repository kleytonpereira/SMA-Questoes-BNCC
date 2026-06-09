"""Carrega e formata as habilidades da BNCC de Matemática."""
import json

def load_habilidades(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def format_habilidades(habilidades: list[dict]) -> str:
    return "\n".join(f"{h['codigo']}: {h['descricao']}" for h in habilidades)
