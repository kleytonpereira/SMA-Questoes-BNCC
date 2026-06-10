"""Fábrica de instâncias de LLM local via Ollama."""
from langchain_ollama import ChatOllama
import config

def make_llm(model: str, temperature: float) -> ChatOllama:
    """Cria um ChatOllama apontando para o servidor Ollama configurado."""
    return ChatOllama(
        model=model,
        temperature=temperature,
        base_url=config.OLLAMA_BASE_URL,
    )
