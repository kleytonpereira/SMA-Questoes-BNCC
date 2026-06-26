"""Montagem do grafo LangGraph e fábrica da aplicação com LLMs reais."""
from langgraph.graph import StateGraph, START, END

import config
from graph.state import EstadoQuestao
from graph.router import (
    decide_apos_validador,
    decide_apos_verificador,
    decide_apos_avaliador,
    decide_apos_avaliador_final,
)


def build_workflow(gerador_node, validador_regras_node, verificador_node,
                   avaliador_node, avaliador_final_node, organizador_node):
    """Monta e compila o grafo a partir das funções-nó injetadas."""
    g = StateGraph(EstadoQuestao)
    g.add_node("gerador", gerador_node)
    g.add_node("validador_regras", validador_regras_node)
    g.add_node("verificador", verificador_node)
    g.add_node("avaliador", avaliador_node)
    g.add_node("avaliador_final", avaliador_final_node)
    g.add_node("organizador", organizador_node)

    g.add_edge(START, "gerador")
    g.add_edge("gerador", "validador_regras")
    g.add_conditional_edges(
        "validador_regras",
        decide_apos_validador,
        {"gerador": "gerador", "verificador": "verificador"},
    )
    g.add_conditional_edges(
        "verificador",
        decide_apos_verificador,
        {"gerador": "gerador", "avaliador": "avaliador"},
    )
    g.add_conditional_edges(
        "avaliador",
        decide_apos_avaliador,
        {"gerador": "gerador", "avaliador_final": "avaliador_final"},
    )
    g.add_conditional_edges(
        "avaliador_final",
        decide_apos_avaliador_final,
        {"gerador": "gerador", "organizador": "organizador"},
    )
    g.add_edge("organizador", END)
    return g.compile()


def create_app():
    """Cria a aplicação com os agentes reais (Ollama). Usada pela interface."""
    from agents.llm_factory import make_structured_llm
    from agents.schemas import Questao, Avaliacao, Classificacao, Resolucao
    from agents.gerador import make_gerador_node
    from agents.validador_regras import make_validador_regras_node
    from agents.verificador import make_verificador_node
    from agents.avaliador import make_avaliador_node, make_avaliador_final_node
    from agents.organizador import make_organizador_node
    from bncc.loader import load_habilidades, format_habilidades

    habilidades_texto = format_habilidades(load_habilidades(config.BNCC_DATA_PATH))

    gerador = make_gerador_node(
        make_structured_llm(config.GENERATOR_MODEL, config.GENERATOR_TEMPERATURE, Questao)
    )
    validador_regras = make_validador_regras_node()
    verificador = make_verificador_node(
        make_structured_llm(config.GENERATOR_MODEL, config.VERIFIER_TEMPERATURE, Resolucao),
        config.VERIFIER_SAMPLES,
    )
    avaliador = make_avaliador_node(
        make_structured_llm(config.EVALUATOR_MODEL, config.EVALUATOR_TEMPERATURE, Avaliacao)
    )
    avaliador_final = make_avaliador_final_node(
        make_structured_llm(config.STRONG_EVALUATOR_MODEL, config.STRONG_EVALUATOR_TEMPERATURE, Avaliacao)
    )
    organizador = make_organizador_node(
        make_structured_llm(config.ORGANIZER_MODEL, config.ORGANIZER_TEMPERATURE, Classificacao),
        habilidades_texto,
    )
    return build_workflow(
        gerador, validador_regras, verificador, avaliador, avaliador_final, organizador
    )
