"""Interface Streamlit do SMA de geração de questões educacionais."""
import streamlit as st

import config
from agents.schemas import format_questao
from graph.workflow import create_app

st.set_page_config(page_title="SMA — Questões BNCC", page_icon="📘")


@st.cache_resource
def get_app():
    """Compila o grafo uma única vez por sessão."""
    return create_app()


def estado_inicial(tema: str) -> dict:
    return {
        "tema": tema,
        "tentativas": 0,
        "questao": {},
        "quality_passed": False,
        "motivo_rejeicao": "",
        "habilidade_bncc": "",
        "descricao_bncc": "",
    }


ROTULOS = {
    "gerador": "✍️ Gerando questão...",
    "avaliador": "🔍 Avaliando qualidade...",
    "organizador": "🏷️ Classificando pela BNCC...",
}

st.title("📘 Gerador de Questões BNCC")
st.caption(
    "Sistema Multiagente (Gerador → Avaliador → Organizador) · Matemática · Ensino Médio"
)

tema = st.text_input(
    "Tema ou código BNCC",
    placeholder="Ex: 'funções do 2º grau' ou 'EM13MAT302'",
)

st.caption("Exemplos rápidos:")
col1, col2, col3 = st.columns(3)
if col1.button("Funções do 2º grau"):
    tema = "funções do 2º grau"
if col2.button("Probabilidade"):
    tema = "probabilidade"
if col3.button("EM13MAT302"):
    tema = "EM13MAT302"

if st.button("Gerar Questão", type="primary") or (tema and tema.strip()):
    if not tema or not tema.strip():
        st.warning("Digite um tema ou código BNCC.")
        st.stop()

    try:
        app = get_app()
        estado_final = None
        with st.status("Executando agentes...", expanded=True) as status:
            for evento in app.stream(estado_inicial(tema.strip())):
                for no, update in evento.items():
                    st.write(ROTULOS.get(no, no))
                    estado_final = {**(estado_final or {}), **update}
            status.update(label="Concluído", state="complete")
    except Exception as e:
        st.error(
            "Não foi possível executar os agentes. Verifique se o Ollama está "
            f"rodando e se o modelo foi baixado (`ollama pull {config.GENERATOR_MODEL}`).\n\n"
            f"Detalhe técnico: {e}"
        )
        st.stop()

    questao = estado_final["questao"]
    aprovada = estado_final["quality_passed"]
    tentativas = estado_final["tentativas"]

    st.divider()
    if aprovada:
        st.success(f"✓ Aprovada na tentativa {tentativas}")
    else:
        st.warning(
            f"⚠️ Limite de {config.MAX_TENTATIVAS} tentativas atingido sem aprovação. "
            "A questão abaixo pode conter problemas."
        )

    st.subheader("Questão")
    st.markdown(format_questao(questao).replace("\n", "  \n"))

    with st.expander("Ver gabarito e explicação"):
        st.markdown(f"**Gabarito:** {questao['gabarito']}")
        st.markdown(f"**Explicação:** {questao['explicacao']}")

    st.subheader("Classificação BNCC")
    st.markdown(f"**{estado_final['habilidade_bncc']}** — {estado_final['descricao_bncc']}")
