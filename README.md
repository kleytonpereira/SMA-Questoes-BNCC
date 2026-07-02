# SMA — Geração e Validação de Questões Educacionais

Sistema Multiagente (LangGraph) que gera questões de múltipla escolha de
Matemática para o Ensino Médio, alinhadas à BNCC, usando LLMs locais via
Ollama. Pipeline de 6 agentes com múltiplas camadas de verificação de
qualidade antes de entregar a questão — veja [Arquitetura](#arquitetura).

## Pré-requisitos

1. **Python 3.11+**
2. **[Ollama](https://ollama.com)** instalado
3. **GPU/CPU** suficiente para rodar modelos ~4B (funciona em CPU, mas é mais lento)

## Instalação

```powershell
# 1. Clonar e entrar na pasta
git clone <url-do-repo>
cd SMA-Questoes

# 2. Ambiente virtual
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Variáveis de ambiente
copy .env.example .env   # ajuste se quiser trocar modelos
```

### Suba o Ollama e baixe os modelos

Em um terminal separado (deixe rodando):

```powershell
ollama serve
```

Em outro terminal, baixe os modelos usados pelo pipeline (os mesmos do `.env.example`):

```powershell
ollama pull qwen3:4b
ollama pull gemma4:12b
```

> ⚠️ **Não use `qwen3.5:4b`** como `GENERATOR_MODEL`/`EVALUATOR_MODEL`/etc.
> Esse modelo ignora a restrição de saída estruturada (`format`/JSON-schema)
> do Ollama e gera texto livre em vez de JSON, quebrando o pipeline com
> `OutputParserException` no agente Gerador. Use `qwen3:4b`, `gemma3:4b`,
> `phi4-mini` ou `llama3.2:3b` — todos respeitam saída estruturada.

Confirme que o Ollama está respondendo antes de seguir:

```powershell
curl http://localhost:11434/api/version
```

## Executar

Com o Ollama no ar (passo anterior), em outro terminal:

```powershell
streamlit run app.py
```

Abra `http://localhost:8501`, digite um tema (ex.: "funções do 2º grau") ou
um código BNCC (ex.: "EM13MAT302") e clique em **Gerar Questão**.

## Testes

```powershell
python -m pytest -v
```

## Configuração

Todas as opções ficam no `.env` (veja `.env.example` para os valores padrão):

| Variável | Para quê |
|---|---|
| `OLLAMA_BASE_URL` | endereço do servidor Ollama |
| `GENERATOR_MODEL` / `EVALUATOR_MODEL` / `STRONG_EVALUATOR_MODEL` / `ORGANIZER_MODEL` | modelo usado por cada agente — troque para comparar modelos 4B |
| `VERIFIER_SAMPLES` / `VERIFIER_TEMPERATURE` | nº de re-soluções e temperatura do agente Verificador (auto-consistência) |
| `REGRA_TERMOS_ABSOLUTOS` | liga/desliga a checagem de termos como "sempre"/"nunca" no Validador de Regras |
| `LANGSMITH_*` | opcional — tracing/observabilidade das chamadas de LLM em [smith.langchain.com](https://smith.langchain.com) |

`MAX_TENTATIVAS` (retries por ciclo) e `MAX_CICLOS` (ciclos completos antes de
entregar com aviso) estão em [config.py](config.py).

## Arquitetura

```
START → gerador → validador_regras → verificador → avaliador → avaliador_final → organizador → END
           ↑___________________↓___________↓____________↓
              (reprovado → volta ao gerador, até esgotar tentativas/ciclos)
```

## Pipeline de agentes (precisão)

`gerador → validador_regras → verificador → avaliador → avaliador_final → organizador`

- **validador_regras** — checagem determinística de item-writing flaws (sem custo de tokens): gabarito válido, alternativas não-vazias/duplicadas, sem "todas/nenhuma das anteriores", sem pista de tamanho na alternativa correta e sem questão tautológica (resposta já contida no enunciado).
- **verificador** — auto-consistência: re-resolve o problema N vezes (voto majoritário) e compara com o gabarito proposto.
- **avaliador** — revisão chain-of-thought (modelo regular): resolve do zero, compara com o gabarito e avalia critérios pedagógicos.
- **avaliador_final** — segunda opinião obrigatória com modelo mais forte.
- **organizador** — classificação na habilidade BNCC.

Falha em qualquer camada antes do organizador devolve a questão ao gerador, respeitando `MAX_TENTATIVAS`. Se o avaliador final reprovar, reinicia um novo ciclo (até `MAX_CICLOS`); esgotados os ciclos, a questão é entregue mesmo assim, com aviso na interface.

Variáveis relevantes no `.env`: `VERIFIER_SAMPLES` (nº de re-soluções), `VERIFIER_TEMPERATURE`, `REGRA_TERMOS_ABSOLUTOS`.

## Troubleshooting

**`OutputParserException: Invalid json output` no Gerador**
O modelo configurado não está respeitando saída estruturada (`format`/JSON-schema)
do Ollama — geralmente por ter escolhido `qwen3.5:4b`. Troque para `qwen3:4b`
(ou outro da lista de modelos recomendados acima) no `.env`.

**`Não foi possível compilar o grafo` / `httpx.ConnectError: [WinError 10061]`**
O Ollama não está rodando. Suba com `ollama serve` (deixe o terminal aberto)
ou abra o aplicativo Ollama, e confirme com `curl http://localhost:11434/api/version`.

**`GraphRecursionError: Recursion limit of 25 reached`**
No pior caso (2 ciclos completos × 3 tentativas) o grafo passa de 25 nós, que é
o limite padrão do LangGraph. O `app.py` já define `recursion_limit=50` na
config do `app.stream(...)` — se você reimplementar a chamada em outro lugar
(script, notebook), lembre de repassar esse limite também.

**Streamlit não reflete uma troca de modelo no `.env`**
`get_app()` usa `@st.cache_resource`, que compila o grafo (e fixa os modelos)
uma única vez por sessão. Reinicie o `streamlit run app.py` depois de editar o `.env`.

**Questões geradas fracas/tautológicas**
Modelos ~4B às vezes geram questões triviais mesmo com o prompt e o validador
de regras cuidando disso. O pipeline existe justamente para pegar esses casos —
se aparecer o aviso de "ciclos completos sem aprovação", considere um
`STRONG_EVALUATOR_MODEL`/`GENERATOR_MODEL` maior (ex.: `qwen2.5:7b`, `qwen3:8b`).

### Fundamentação
- Generating AI Literacy MCQs: A Multi-Agent LLM Approach (arXiv 2412.00970)
- ReQUESTA: Hybrid Agentic Framework for MCQ Generation
- When AIs Judge AIs: Agent-as-a-Judge (arXiv 2508.02994)
