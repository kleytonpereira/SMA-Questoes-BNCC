"""Fábrica de instâncias de LLM local via Ollama."""
from langchain_ollama import ChatOllama
import config


def make_llm(model: str, temperature: float) -> ChatOllama:
    """Cria um ChatOllama apontando para o servidor Ollama configurado.

    reasoning=False desliga o "thinking mode" de modelos como qwen3/qwen3.5,
    que emitem blocos <think> e quebram a saída estruturada.
    """
    return ChatOllama(
        model=model,
        temperature=temperature,
        base_url=config.OLLAMA_BASE_URL,
        reasoning=False,
    )


def make_structured_llm(model: str, temperature: float, schema):
    """LLM com saída estruturada nativa do Ollama (method='json_schema').

    O Ollama restringe gramaticalmente a saída ao schema, garantindo JSON
    válido e valores de enum corretos (ex.: gabarito sempre A-D). Mais robusto
    que o parsing por prompt, sobretudo com modelos pequenos (3-4B).
    """
    return make_llm(model, temperature).with_structured_output(schema, method="json_schema")
