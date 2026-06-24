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
        "ciclos": 0,
        "regras_passed": False,
        "questao": {},
        "quality_passed": False,
        "motivo_rejeicao": "",
        "habilidade_bncc": "",
        "descricao_bncc": "",
    }


ROTULOS = {
    "gerador": "✍️ Gerando questão...",
    "validador_regras": "📋 Checando regras estruturais...",
    "verificador": "🔢 Verificando consistência numérica...",
    "avaliador": "🔍 Avaliando qualidade...",
    "avaliador_final": "🧠 Avaliação final (modelo forte)...",
    "organizador": "🏷️ Classificando pela BNCC...",
}

st.title("📘 Gerador de Questões BNCC")
st.caption(
    "Sistema Multiagente (Gerador → Validador → Verificador → Avaliador → Avaliador Final → Organizador) · Matemática · Ensino Médio"
)

tema = st.text_input(
    "Tema ou código BNCC",
    placeholder="Ex: 'funções do 2º grau' ou 'EM13MAT302'",
)

num_questoes = st.number_input(
    "Número de questões",
    min_value=1,
    max_value=10,
    value=1,
    step=1,
)

st.caption("Exemplos rápidos:")
col1, col2, col3 = st.columns(3)
if col1.button("Funções do 2º grau"):
    tema = "funções do 2º grau"
if col2.button("Probabilidade"):
    tema = "probabilidade"
if col3.button("EM13MAT302"):
    tema = "EM13MAT302"

if st.button("Gerar Questão" if num_questoes == 1 else f"Gerar {num_questoes} Questões", type="primary"):
    if not tema or not tema.strip():
        st.warning("Digite um tema ou código BNCC.")
        st.stop()

    try:
        app = get_app()
    except Exception as e:
        st.error(
            "Não foi possível compilar o grafo. Verifique se o Ollama está rodando.\n\n"
            f"Detalhe técnico: {e}"
        )
        st.stop()

    for i in range(int(num_questoes)):
        if num_questoes > 1:
            st.subheader(f"Questão {i + 1} de {int(num_questoes)}")

        try:
            estado_final = None
            with st.status(f"Executando agentes{'...' if num_questoes == 1 else f' (questão {i+1})'}...", expanded=True) as status:
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
            continue

        questao = estado_final["questao"]
        aprovada = estado_final["quality_passed"]
        tentativas = estado_final["tentativas"]
        ciclos = estado_final.get("ciclos", 0)

        st.divider()
        if aprovada:
            st.success(f"✓ Aprovada na tentativa {tentativas}")
        elif ciclos >= config.MAX_CICLOS:
            st.warning(
                f"⚠️ {config.MAX_CICLOS} ciclos completos sem aprovação pelo avaliador forte. "
                "A questão abaixo pode conter problemas matemáticos."
            )
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
