# SMA para Geração e Validação de Questões Educacionais — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir um Sistema Multiagente (Gerador → Avaliador → Organizador) em Python/LangGraph que gera questões de múltipla escolha de Matemática para o Ensino Médio alinhadas à BNCC, com loop de retry por qualidade e interface Streamlit.

**Architecture:** Pipeline LangGraph com quality gate. O Gerador cria a questão, o Avaliador aprova ou rejeita (com motivo), e um roteador decide entre regerar (até 3 tentativas) ou seguir para o Organizador, que classifica pela BNCC. Cada agente recebe seu LLM por injeção de dependência, o que torna toda a lógica testável sem o Ollama rodando.

**Tech Stack:** Python 3.11+, LangGraph, langchain-ollama (ChatOllama), Streamlit, Pydantic v2, python-dotenv, pytest. Modelo local padrão: `qwen2.5:7b` via Ollama.

---

## Estrutura de Arquivos

A spec define `app.py`, `agents/`, `graph/`, `data/`, `config.py`. Este plano adiciona arquivos pequenos e focados para tornar a lógica testável (cada um com responsabilidade única):

```
SMA-Questoes/
├── app.py                      # Interface Streamlit (entrada, progresso, resultado)
├── config.py                   # Parâmetros e variáveis de ambiente
├── conftest.py                 # Âncora de rootdir do pytest (vazio)
├── requirements.txt
├── .env.example
├── .gitignore
├── agents/
│   ├── __init__.py
│   ├── schemas.py              # Modelos Pydantic (Questao, Avaliacao, Classificacao) + format_questao
│   ├── llm_factory.py          # make_llm(model, temperature) -> ChatOllama
│   ├── gerador.py              # build_gerador_messages + make_gerador_node
│   ├── avaliador.py            # build_avaliador_messages + make_avaliador_node
│   └── organizador.py          # build_organizador_messages + make_organizador_node
├── graph/
│   ├── __init__.py
│   ├── state.py                # EstadoQuestao (TypedDict)
│   ├── router.py               # decide_proximo (lógica do loop — puro)
│   └── workflow.py             # build_workflow (wiring) + create_app (deps reais)
├── bncc/
│   ├── __init__.py
│   └── loader.py               # load_habilidades + format_habilidades
├── data/
│   └── bncc_matematica.json    # Habilidades EM13MAT* (subconjunto inicial)
└── tests/
    ├── test_schemas.py
    ├── test_bncc_loader.py
    ├── test_llm_factory.py
    ├── test_gerador.py
    ├── test_avaliador.py
    ├── test_organizador.py
    ├── test_router.py
    └── test_workflow.py
```

**Padrão de testabilidade:** Cada agente expõe (1) uma função pura `build_*_messages(...)` que monta o prompt e (2) uma fábrica `make_*_node(structured_llm, ...)` que devolve a função-nó `node(state) -> dict`. Em produção, `structured_llm = llm.with_structured_output(Schema)`. Nos testes, injetamos um `RunnableLambda` falso que devolve um objeto Pydantic — assim os testes rodam sem Ollama.

**Convenção de execução de testes:** sempre rodar a partir da raiz do projeto com `python -m pytest` (insere a raiz no `sys.path`, resolvendo `import config`, `import agents.gerador`, etc.).

---

### Task 1: Scaffolding e dependências

**Files:**
- Create: `requirements.txt`, `.gitignore`, `.env.example`, `config.py`, `conftest.py`
- Create (vazios): `agents/__init__.py`, `graph/__init__.py`, `bncc/__init__.py`

- [ ] **Step 1: Criar `requirements.txt`**

```
langgraph>=0.2,<0.4
langchain-ollama>=0.2,<0.4
langchain-core>=0.3,<0.4
streamlit>=1.40
pydantic>=2.7
python-dotenv>=1.0
pytest>=8.0
```

- [ ] **Step 2: Criar `.gitignore`**

```
.venv/
__pycache__/
*.pyc
.env
.pytest_cache/
.superpowers/
```

- [ ] **Step 3: Criar `.env.example`**

```env
# URL do servidor Ollama local
OLLAMA_BASE_URL=http://localhost:11434

# Modelos por agente (padrão: qwen2.5:7b via Ollama)
GENERATOR_MODEL=qwen2.5:7b
# Para usar um modelo mais potente no Avaliador, troque aqui. Exemplos:
#   EVALUATOR_MODEL=llama3.1:70b
#   EVALUATOR_MODEL=qwen2.5:14b
EVALUATOR_MODEL=qwen2.5:7b
ORGANIZER_MODEL=qwen2.5:7b
```

- [ ] **Step 4: Criar `config.py`**

```python
"""Configuração central do SMA. Lê variáveis de ambiente do .env."""
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

GENERATOR_MODEL = os.getenv("GENERATOR_MODEL", "qwen2.5:7b")
EVALUATOR_MODEL = os.getenv("EVALUATOR_MODEL", "qwen2.5:7b")
ORGANIZER_MODEL = os.getenv("ORGANIZER_MODEL", "qwen2.5:7b")

# Temperaturas: Gerador criativo, Avaliador e Organizador precisos
GENERATOR_TEMPERATURE = 0.7
EVALUATOR_TEMPERATURE = 0.1
ORGANIZER_TEMPERATURE = 0.1

# Número máximo de gerações antes de entregar mesmo sem aprovação
MAX_TENTATIVAS = 3

BNCC_DATA_PATH = "data/bncc_matematica.json"
```

- [ ] **Step 5: Criar `conftest.py` (vazio) e os `__init__.py` (vazios)**

`conftest.py` na raiz pode estar vazio — sua presença ancora o rootdir do pytest. Criar também `agents/__init__.py`, `graph/__init__.py`, `bncc/__init__.py` vazios.

- [ ] **Step 6: Criar venv e instalar dependências**

Run (PowerShell, na raiz do projeto):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Expected: instalação concluída sem erros.

- [ ] **Step 7: Verificar que o config importa**

Run: `python -c "import config; print(config.GENERATOR_MODEL)"`
Expected: imprime `qwen2.5:7b`

- [ ] **Step 8: Commit**

```bash
git add requirements.txt .gitignore .env.example config.py conftest.py agents/__init__.py graph/__init__.py bncc/__init__.py
git commit -m "chore: scaffolding do projeto e dependências"
```

---

### Task 2: Schemas Pydantic

**Files:**
- Create: `agents/schemas.py`
- Test: `tests/test_schemas.py`

**Decisão de design:** as alternativas são campos planos (`alternativa_a..d`), não um dict. Esquemas planos são muito mais confiáveis com modelos pequenos (7B) na saída estruturada. O gabarito usa `Literal["A","B","C","D"]` para validação automática.

- [ ] **Step 1: Escrever os testes que falham**

```python
# tests/test_schemas.py
import pytest
from pydantic import ValidationError
from agents.schemas import Questao, Avaliacao, Classificacao, format_questao


def make_questao(**kw):
    base = dict(
        enunciado="Qual o valor de 2+2?",
        alternativa_a="3",
        alternativa_b="4",
        alternativa_c="5",
        alternativa_d="6",
        gabarito="B",
        explicacao="2+2=4",
    )
    base.update(kw)
    return base


def test_questao_valida():
    q = Questao(**make_questao())
    assert q.gabarito == "B"
    assert q.alternativa_b == "4"


def test_questao_gabarito_invalido_levanta_erro():
    with pytest.raises(ValidationError):
        Questao(**make_questao(gabarito="E"))


def test_avaliacao_valida():
    a = Avaliacao(quality_passed=False, motivo="Gabarito incorreto")
    assert a.quality_passed is False
    assert "incorreto" in a.motivo


def test_classificacao_valida():
    c = Classificacao(codigo_bncc="EM13MAT302", descricao_habilidade="Funções quadráticas")
    assert c.codigo_bncc == "EM13MAT302"


def test_format_questao_inclui_enunciado_e_alternativas():
    texto = format_questao(make_questao())
    assert "Qual o valor de 2+2?" in texto
    assert "A) 3" in texto
    assert "B) 4" in texto
    assert "C) 5" in texto
    assert "D) 6" in texto
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_schemas.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.schemas'`

- [ ] **Step 3: Implementar `agents/schemas.py`**

```python
"""Modelos Pydantic usados na saída estruturada dos agentes."""
from typing import Literal
from pydantic import BaseModel, Field


class Questao(BaseModel):
    """Questão de múltipla escolha gerada pelo Agente Gerador."""
    enunciado: str = Field(description="Enunciado completo da questão")
    alternativa_a: str = Field(description="Texto da alternativa A")
    alternativa_b: str = Field(description="Texto da alternativa B")
    alternativa_c: str = Field(description="Texto da alternativa C")
    alternativa_d: str = Field(description="Texto da alternativa D")
    gabarito: Literal["A", "B", "C", "D"] = Field(description="Letra da alternativa correta")
    explicacao: str = Field(description="Explicação de por que o gabarito está correto")


class Avaliacao(BaseModel):
    """Veredito do Agente Avaliador sobre uma questão."""
    quality_passed: bool = Field(description="True se a questão atende a todos os critérios")
    motivo: str = Field(description="Justificativa; descreve o problema quando reprovada")


class Classificacao(BaseModel):
    """Classificação BNCC produzida pelo Agente Organizador."""
    codigo_bncc: str = Field(description="Código da habilidade, ex: EM13MAT302")
    descricao_habilidade: str = Field(description="Descrição da habilidade classificada")


def format_questao(questao: dict) -> str:
    """Formata uma questão (dict) como texto legível para prompts e exibição."""
    return (
        f"{questao['enunciado']}\n"
        f"A) {questao['alternativa_a']}\n"
        f"B) {questao['alternativa_b']}\n"
        f"C) {questao['alternativa_c']}\n"
        f"D) {questao['alternativa_d']}"
    )
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_schemas.py -v`
Expected: PASS (5 testes)

- [ ] **Step 5: Commit**

```bash
git add agents/schemas.py tests/test_schemas.py
git commit -m "feat: schemas Pydantic dos agentes e formatador de questão"
```

---

### Task 3: Estado do grafo

**Files:**
- Create: `graph/state.py`
- Test: `tests/test_state.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_state.py
from graph.state import EstadoQuestao


def test_estado_aceita_campos_esperados():
    estado: EstadoQuestao = {
        "tema": "funções do 2º grau",
        "tentativas": 0,
        "questao": {},
        "quality_passed": False,
        "motivo_rejeicao": "",
        "habilidade_bncc": "",
        "descricao_bncc": "",
    }
    assert estado["tema"] == "funções do 2º grau"
    assert estado["tentativas"] == 0
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_state.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'graph.state'`

- [ ] **Step 3: Implementar `graph/state.py`**

```python
"""Estado compartilhado entre os nós do grafo LangGraph."""
from typing import TypedDict


class EstadoQuestao(TypedDict):
    tema: str                # entrada do usuário (tema livre ou código BNCC)
    tentativas: int          # contador de gerações (inicia em 0)
    questao: dict            # saída do Agente Gerador (Questao.model_dump())
    quality_passed: bool     # flag de aprovação do Avaliador
    motivo_rejeicao: str     # feedback do Avaliador para o Gerador
    habilidade_bncc: str     # código classificado pelo Organizador
    descricao_bncc: str      # descrição da habilidade classificada
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_state.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add graph/state.py tests/test_state.py
git commit -m "feat: estado compartilhado do grafo"
```

---

### Task 4: Dados e loader da BNCC

**Files:**
- Create: `data/bncc_matematica.json`
- Create: `bncc/loader.py`
- Test: `tests/test_bncc_loader.py`

**Nota sobre os dados:** o JSON abaixo é um subconjunto inicial de habilidades reais de Matemática do Ensino Médio (códigos EM13MAT*). É suficiente para o protótipo funcionar. Para a versão final do artigo, expanda/confira as descrições com o documento oficial da BNCC (PDF "BNCC Matemática e suas Tecnologias" já em mãos da equipe).

- [ ] **Step 1: Criar `data/bncc_matematica.json`**

```json
[
  {"codigo": "EM13MAT101", "descricao": "Interpretar criticamente situações econômicas, sociais e fatos relativos às Ciências da Natureza que envolvam a variação de grandezas, pela análise de gráficos, tabelas e relações algébricas."},
  {"codigo": "EM13MAT104", "descricao": "Interpretar taxas e índices de natureza socioeconômica, investigando os processos de cálculo desses números, para analisar criticamente a realidade e produzir argumentos."},
  {"codigo": "EM13MAT203", "descricao": "Aplicar conceitos matemáticos no planejamento, na execução e na análise de ações envolvendo a utilização de aplicativos e a criação de planilhas."},
  {"codigo": "EM13MAT301", "descricao": "Resolver e elaborar problemas do cotidiano, da Matemática e de outras áreas do conhecimento, que envolvem equações lineares simultâneas, usando técnicas algébricas e gráficas."},
  {"codigo": "EM13MAT302", "descricao": "Construir modelos empregando as funções polinomiais de 1º ou 2º graus, para resolver problemas em contextos diversos, com ou sem apoio de tecnologias digitais."},
  {"codigo": "EM13MAT303", "descricao": "Interpretar e comparar situações que envolvam juros simples com as que envolvem juros compostos, por meio de representações gráficas e análise de planilhas."},
  {"codigo": "EM13MAT304", "descricao": "Resolver e elaborar problemas com funções exponenciais nos quais seja necessário compreender e interpretar a variação das grandezas envolvidas."},
  {"codigo": "EM13MAT305", "descricao": "Resolver e elaborar problemas com funções logarítmicas nos quais seja necessário compreender e interpretar a variação das grandezas envolvidas."},
  {"codigo": "EM13MAT306", "descricao": "Resolver e elaborar problemas em contextos que envolvem fenômenos periódicos reais e comparar suas representações com as funções seno e cosseno."},
  {"codigo": "EM13MAT308", "descricao": "Aplicar as relações métricas, incluindo as leis do seno e do cosseno ou as relações de proporcionalidade, na resolução de problemas envolvendo triângulos."},
  {"codigo": "EM13MAT401", "descricao": "Converter representações algébricas de funções polinomiais de 1º grau em representações geométricas no plano cartesiano, distinguindo casos de retas paralelas e perpendiculares."},
  {"codigo": "EM13MAT402", "descricao": "Converter representações algébricas de funções polinomiais de 2º grau em representações geométricas no plano cartesiano, distinguindo concavidade, vértice, zeros e eixo de simetria."},
  {"codigo": "EM13MAT406", "descricao": "Construir e interpretar tabelas e gráficos de frequências com base em dados obtidos em pesquisas, usando medidas de tendência central (média, moda e mediana) e de dispersão (amplitude e desvio padrão)."},
  {"codigo": "EM13MAT507", "descricao": "Identificar e descrever o espaço amostral de eventos aleatórios, realizando contagem das possibilidades, para resolver e elaborar problemas que envolvem o cálculo da probabilidade."},
  {"codigo": "EM13MAT510", "descricao": "Investigar conjuntos de dados relativos ao comportamento de duas variáveis numéricas, usando ou não tecnologias da informação, e estimar regularidades ou tendências."},
  {"codigo": "EM13MAT511", "descricao": "Reconhecer a existência de diferentes tipos de espaços amostrais, discretos ou não, e de eventos, e usar processos de contagem como o princípio multiplicativo, arranjos, combinações e permutações."}
]
```

- [ ] **Step 2: Escrever os testes que falham**

```python
# tests/test_bncc_loader.py
from bncc.loader import load_habilidades, format_habilidades


def test_load_habilidades_retorna_lista_com_codigo_e_descricao():
    habilidades = load_habilidades("data/bncc_matematica.json")
    assert isinstance(habilidades, list)
    assert len(habilidades) >= 10
    primeira = habilidades[0]
    assert "codigo" in primeira
    assert "descricao" in primeira
    assert primeira["codigo"].startswith("EM13MAT")


def test_format_habilidades_gera_linhas_codigo_descricao():
    habilidades = [
        {"codigo": "EM13MAT302", "descricao": "Funções polinomiais de 1º ou 2º graus."},
        {"codigo": "EM13MAT507", "descricao": "Probabilidade."},
    ]
    texto = format_habilidades(habilidades)
    assert "EM13MAT302: Funções polinomiais de 1º ou 2º graus." in texto
    assert "EM13MAT507: Probabilidade." in texto
    assert texto.count("\n") == 1  # duas linhas, uma quebra
```

- [ ] **Step 3: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_bncc_loader.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'bncc.loader'`

- [ ] **Step 4: Implementar `bncc/loader.py`**

```python
"""Carrega e formata as habilidades da BNCC de Matemática."""
import json


def load_habilidades(path: str) -> list[dict]:
    """Lê o JSON de habilidades da BNCC e devolve uma lista de dicts."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def format_habilidades(habilidades: list[dict]) -> str:
    """Formata as habilidades como linhas 'CODIGO: descrição' para o prompt."""
    return "\n".join(f"{h['codigo']}: {h['descricao']}" for h in habilidades)
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_bncc_loader.py -v`
Expected: PASS (2 testes)

- [ ] **Step 6: Commit**

```bash
git add data/bncc_matematica.json bncc/loader.py tests/test_bncc_loader.py
git commit -m "feat: dados BNCC de Matemática e loader"
```

---

### Task 5: Fábrica de LLM

**Files:**
- Create: `agents/llm_factory.py`
- Test: `tests/test_llm_factory.py`

**Nota:** instanciar `ChatOllama` não abre conexão com o servidor — só configura o cliente. Por isso o teste roda sem Ollama.

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_llm_factory.py
from agents.llm_factory import make_llm


def test_make_llm_configura_modelo_e_temperatura():
    llm = make_llm("qwen2.5:7b", 0.7)
    assert llm.model == "qwen2.5:7b"
    assert llm.temperature == 0.7
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_llm_factory.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.llm_factory'`

- [ ] **Step 3: Implementar `agents/llm_factory.py`**

```python
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
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_llm_factory.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agents/llm_factory.py tests/test_llm_factory.py
git commit -m "feat: fábrica de LLM via Ollama"
```

---

### Task 6: Agente Gerador

**Files:**
- Create: `agents/gerador.py`
- Test: `tests/test_gerador.py`

- [ ] **Step 1: Escrever os testes que falham**

```python
# tests/test_gerador.py
from langchain_core.runnables import RunnableLambda
from agents.gerador import build_gerador_messages, make_gerador_node
from agents.schemas import Questao


def questao_fake() -> Questao:
    return Questao(
        enunciado="Qual o vértice de y=x²?",
        alternativa_a="(0,0)",
        alternativa_b="(1,1)",
        alternativa_c="(0,1)",
        alternativa_d="(1,0)",
        gabarito="A",
        explicacao="O vértice de y=x² é a origem.",
    )


def test_build_messages_primeira_tentativa_inclui_tema_sem_rejeicao():
    msgs = build_gerador_messages("funções do 2º grau", "")
    conteudo = " ".join(m.content for m in msgs)
    assert "funções do 2º grau" in conteudo
    assert "REJEITADA" not in conteudo


def test_build_messages_retry_inclui_motivo_rejeicao():
    msgs = build_gerador_messages("funções", "Alternativa C incorreta")
    conteudo = " ".join(m.content for m in msgs)
    assert "Alternativa C incorreta" in conteudo
    assert "REJEITADA" in conteudo


def test_gerador_node_incrementa_tentativas_e_salva_questao():
    fake_llm = RunnableLambda(lambda _: questao_fake())
    node = make_gerador_node(fake_llm)
    update = node({"tema": "funções", "tentativas": 0, "motivo_rejeicao": ""})
    assert update["tentativas"] == 1
    assert update["questao"]["gabarito"] == "A"
    assert update["questao"]["enunciado"] == "Qual o vértice de y=x²?"


def test_gerador_node_incrementa_a_partir_do_valor_atual():
    fake_llm = RunnableLambda(lambda _: questao_fake())
    node = make_gerador_node(fake_llm)
    update = node({"tema": "funções", "tentativas": 1, "motivo_rejeicao": "erro"})
    assert update["tentativas"] == 2
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_gerador.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.gerador'`

- [ ] **Step 3: Implementar `agents/gerador.py`**

```python
"""Agente Gerador: cria questões de múltipla escolha."""
from langchain_core.messages import SystemMessage, HumanMessage

SYSTEM_PROMPT = (
    "Você é um professor especialista em Matemática do Ensino Médio brasileiro. "
    "Sua tarefa é criar UMA questão de múltipla escolha alinhada à BNCC, com "
    "exatamente quatro alternativas (A, B, C e D), das quais apenas UMA é correta. "
    "As alternativas incorretas devem ser plausíveis (erros comuns dos alunos), "
    "nunca absurdas. Use linguagem adequada ao Ensino Médio e forneça uma "
    "explicação clara do gabarito."
)


def build_gerador_messages(tema: str, motivo_rejeicao: str) -> list:
    """Monta as mensagens do Gerador. Inclui o feedback de rejeição em retries."""
    humano = f"Tema solicitado: {tema}\n\nGere a questão."
    if motivo_rejeicao:
        humano += (
            "\n\nATENÇÃO: a tentativa anterior foi REJEITADA pelo revisor com a "
            f'seguinte justificativa:\n"{motivo_rejeicao}"\n'
            "Corrija especificamente esse problema na nova questão."
        )
    return [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=humano)]


def make_gerador_node(structured_llm):
    """Devolve a função-nó do Gerador, usando o LLM estruturado injetado."""
    def gerador_node(state: dict) -> dict:
        msgs = build_gerador_messages(state["tema"], state.get("motivo_rejeicao", ""))
        questao = structured_llm.invoke(msgs)
        return {
            "tentativas": state["tentativas"] + 1,
            "questao": questao.model_dump(),
        }
    return gerador_node
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_gerador.py -v`
Expected: PASS (4 testes)

- [ ] **Step 5: Commit**

```bash
git add agents/gerador.py tests/test_gerador.py
git commit -m "feat: Agente Gerador com suporte a feedback de retry"
```

---

### Task 7: Agente Avaliador

**Files:**
- Create: `agents/avaliador.py`
- Test: `tests/test_avaliador.py`

- [ ] **Step 1: Escrever os testes que falham**

```python
# tests/test_avaliador.py
from langchain_core.runnables import RunnableLambda
from agents.avaliador import build_avaliador_messages, make_avaliador_node
from agents.schemas import Avaliacao

QUESTAO = {
    "enunciado": "Qual o vértice de y=x²?",
    "alternativa_a": "(0,0)",
    "alternativa_b": "(1,1)",
    "alternativa_c": "(0,1)",
    "alternativa_d": "(1,0)",
    "gabarito": "A",
    "explicacao": "O vértice de y=x² é a origem.",
}


def test_build_messages_inclui_tema_e_questao():
    msgs = build_avaliador_messages("funções do 2º grau", QUESTAO)
    conteudo = " ".join(m.content for m in msgs)
    assert "funções do 2º grau" in conteudo
    assert "Qual o vértice de y=x²?" in conteudo
    assert "A) (0,0)" in conteudo


def test_avaliador_node_aprovada_define_quality_passed_true_e_limpa_motivo():
    fake_llm = RunnableLambda(lambda _: Avaliacao(quality_passed=True, motivo="Aprovada"))
    node = make_avaliador_node(fake_llm)
    update = node({"tema": "funções", "questao": QUESTAO})
    assert update["quality_passed"] is True
    assert update["motivo_rejeicao"] == ""


def test_avaliador_node_reprovada_propaga_motivo():
    fake_llm = RunnableLambda(
        lambda _: Avaliacao(quality_passed=False, motivo="Gabarito incorreto")
    )
    node = make_avaliador_node(fake_llm)
    update = node({"tema": "funções", "questao": QUESTAO})
    assert update["quality_passed"] is False
    assert update["motivo_rejeicao"] == "Gabarito incorreto"
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_avaliador.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.avaliador'`

- [ ] **Step 3: Implementar `agents/avaliador.py`**

```python
"""Agente Avaliador: aprova ou rejeita a questão gerada."""
from langchain_core.messages import SystemMessage, HumanMessage

from agents.schemas import format_questao

SYSTEM_PROMPT = (
    "Você é um revisor pedagógico rigoroso de questões de Matemática do Ensino "
    "Médio. Avalie a questão segundo os critérios:\n"
    "1. O gabarito está matematicamente correto e é a ÚNICA alternativa correta.\n"
    "2. As alternativas erradas são plausíveis e não óbvias.\n"
    "3. A linguagem é adequada ao Ensino Médio.\n"
    "4. A questão corresponde ao tema solicitado.\n"
    "5. O enunciado não é ambíguo.\n"
    "Se TODOS os critérios forem atendidos, aprove (quality_passed=true). Caso "
    "contrário, reprove (quality_passed=false) e descreva objetivamente o "
    "problema principal no campo 'motivo'."
)


def build_avaliador_messages(tema: str, questao: dict) -> list:
    """Monta as mensagens do Avaliador a partir do tema e da questão gerada."""
    humano = (
        f"Tema solicitado: {tema}\n\n"
        f"Questão a avaliar:\n{format_questao(questao)}\n"
        f"Gabarito informado: {questao['gabarito']}\n"
        f"Explicação informada: {questao['explicacao']}"
    )
    return [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=humano)]


def make_avaliador_node(structured_llm):
    """Devolve a função-nó do Avaliador, usando o LLM estruturado injetado."""
    def avaliador_node(state: dict) -> dict:
        msgs = build_avaliador_messages(state["tema"], state["questao"])
        avaliacao = structured_llm.invoke(msgs)
        return {
            "quality_passed": avaliacao.quality_passed,
            "motivo_rejeicao": "" if avaliacao.quality_passed else avaliacao.motivo,
        }
    return avaliador_node
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_avaliador.py -v`
Expected: PASS (3 testes)

- [ ] **Step 5: Commit**

```bash
git add agents/avaliador.py tests/test_avaliador.py
git commit -m "feat: Agente Avaliador com quality gate"
```

---

### Task 8: Agente Organizador

**Files:**
- Create: `agents/organizador.py`
- Test: `tests/test_organizador.py`

- [ ] **Step 1: Escrever os testes que falham**

```python
# tests/test_organizador.py
from langchain_core.runnables import RunnableLambda
from agents.organizador import build_organizador_messages, make_organizador_node
from agents.schemas import Classificacao

QUESTAO = {
    "enunciado": "Qual o vértice de y=x²?",
    "alternativa_a": "(0,0)",
    "alternativa_b": "(1,1)",
    "alternativa_c": "(0,1)",
    "alternativa_d": "(1,0)",
    "gabarito": "A",
    "explicacao": "O vértice de y=x² é a origem.",
}
HABILIDADES_TEXTO = (
    "EM13MAT302: Funções polinomiais de 1º ou 2º graus.\n"
    "EM13MAT507: Probabilidade."
)


def test_build_messages_inclui_habilidades_e_questao():
    msgs = build_organizador_messages(QUESTAO, HABILIDADES_TEXTO)
    conteudo = " ".join(m.content for m in msgs)
    assert "EM13MAT302" in conteudo
    assert "Qual o vértice de y=x²?" in conteudo


def test_organizador_node_salva_codigo_e_descricao():
    fake_llm = RunnableLambda(
        lambda _: Classificacao(codigo_bncc="EM13MAT302", descricao_habilidade="Funções")
    )
    node = make_organizador_node(fake_llm, HABILIDADES_TEXTO)
    update = node({"questao": QUESTAO})
    assert update["habilidade_bncc"] == "EM13MAT302"
    assert update["descricao_bncc"] == "Funções"
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_organizador.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.organizador'`

- [ ] **Step 3: Implementar `agents/organizador.py`**

```python
"""Agente Organizador: classifica a questão segundo a BNCC."""
from langchain_core.messages import SystemMessage, HumanMessage

from agents.schemas import format_questao

SYSTEM_PROMPT = (
    "Você classifica questões de Matemática do Ensino Médio segundo as "
    "habilidades da BNCC. Escolha o ÚNICO código de habilidade mais adequado ao "
    "conteúdo da questão, dentre a lista fornecida. Retorne o código exatamente "
    "como aparece na lista e a descrição correspondente."
)


def build_organizador_messages(questao: dict, habilidades_texto: str) -> list:
    """Monta as mensagens do Organizador com a lista de habilidades e a questão."""
    humano = (
        f"Habilidades disponíveis:\n{habilidades_texto}\n\n"
        f"Questão a classificar:\n{format_questao(questao)}\n\n"
        "Classifique escolhendo o código mais adequado."
    )
    return [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=humano)]


def make_organizador_node(structured_llm, habilidades_texto: str):
    """Devolve a função-nó do Organizador. A lista de habilidades é injetada."""
    def organizador_node(state: dict) -> dict:
        msgs = build_organizador_messages(state["questao"], habilidades_texto)
        classificacao = structured_llm.invoke(msgs)
        return {
            "habilidade_bncc": classificacao.codigo_bncc,
            "descricao_bncc": classificacao.descricao_habilidade,
        }
    return organizador_node
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_organizador.py -v`
Expected: PASS (2 testes)

- [ ] **Step 5: Commit**

```bash
git add agents/organizador.py tests/test_organizador.py
git commit -m "feat: Agente Organizador com classificação BNCC"
```

---

### Task 9: Roteador (lógica do loop)

**Files:**
- Create: `graph/router.py`
- Test: `tests/test_router.py`

**Esta é a lógica determinística mais importante do sistema** — controla o loop de retry. Totalmente testada.

- [ ] **Step 1: Escrever os testes que falham**

```python
# tests/test_router.py
from graph.router import decide_proximo


def test_aprovada_vai_para_organizador():
    assert decide_proximo({"quality_passed": True, "tentativas": 1}) == "organizador"


def test_reprovada_com_tentativas_restantes_volta_para_gerador():
    assert decide_proximo({"quality_passed": False, "tentativas": 1}) == "gerador"
    assert decide_proximo({"quality_passed": False, "tentativas": 2}) == "gerador"


def test_reprovada_no_limite_vai_para_organizador():
    assert decide_proximo({"quality_passed": False, "tentativas": 3}) == "organizador"


def test_aprovada_tem_prioridade_sobre_limite():
    assert decide_proximo({"quality_passed": True, "tentativas": 3}) == "organizador"
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_router.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'graph.router'`

- [ ] **Step 3: Implementar `graph/router.py`**

```python
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
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_router.py -v`
Expected: PASS (4 testes)

- [ ] **Step 5: Commit**

```bash
git add graph/router.py tests/test_router.py
git commit -m "feat: roteador do quality gate com limite de tentativas"
```

---

### Task 10: Montagem do workflow

**Files:**
- Create: `graph/workflow.py`
- Test: `tests/test_workflow.py`

**`build_workflow`** faz só o wiring (testável com nós falsos). **`create_app`** injeta os LLMs reais. O teste de integração exercita o loop completo (rejeita → regera → aprova) sem Ollama.

- [ ] **Step 1: Escrever os testes que falham**

```python
# tests/test_workflow.py
from graph.workflow import build_workflow


def test_workflow_fluxo_feliz_aprovado_na_primeira():
    def gerador(state):
        return {"tentativas": state["tentativas"] + 1, "questao": {"gabarito": "A"}}

    def avaliador(state):
        return {"quality_passed": True, "motivo_rejeicao": ""}

    def organizador(state):
        return {"habilidade_bncc": "EM13MAT302", "descricao_bncc": "Funções"}

    app = build_workflow(gerador, avaliador, organizador)
    final = app.invoke(
        {"tema": "funções", "tentativas": 0, "quality_passed": False, "motivo_rejeicao": ""}
    )
    assert final["tentativas"] == 1
    assert final["quality_passed"] is True
    assert final["habilidade_bncc"] == "EM13MAT302"


def test_workflow_loop_rejeita_uma_vez_depois_aprova():
    chamadas = {"avaliador": 0}

    def gerador(state):
        return {"tentativas": state["tentativas"] + 1, "questao": {"gabarito": "A"}}

    def avaliador(state):
        chamadas["avaliador"] += 1
        if chamadas["avaliador"] == 1:
            return {"quality_passed": False, "motivo_rejeicao": "Gabarito errado"}
        return {"quality_passed": True, "motivo_rejeicao": ""}

    def organizador(state):
        return {"habilidade_bncc": "EM13MAT302", "descricao_bncc": "Funções"}

    app = build_workflow(gerador, avaliador, organizador)
    final = app.invoke(
        {"tema": "funções", "tentativas": 0, "quality_passed": False, "motivo_rejeicao": ""}
    )
    assert chamadas["avaliador"] == 2  # avaliou duas vezes
    assert final["tentativas"] == 2    # gerou duas vezes
    assert final["quality_passed"] is True


def test_workflow_para_no_limite_de_tentativas_sem_aprovacao():
    def gerador(state):
        return {"tentativas": state["tentativas"] + 1, "questao": {"gabarito": "A"}}

    def avaliador(state):
        return {"quality_passed": False, "motivo_rejeicao": "Sempre ruim"}

    def organizador(state):
        return {"habilidade_bncc": "EM13MAT302", "descricao_bncc": "Funções"}

    app = build_workflow(gerador, avaliador, organizador)
    final = app.invoke(
        {"tema": "funções", "tentativas": 0, "quality_passed": False, "motivo_rejeicao": ""}
    )
    assert final["tentativas"] == 3        # parou no MAX_TENTATIVAS
    assert final["quality_passed"] is False
    assert final["habilidade_bncc"] == "EM13MAT302"  # ainda classificou
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_workflow.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'graph.workflow'`

- [ ] **Step 3: Implementar `graph/workflow.py`**

```python
"""Montagem do grafo LangGraph e fábrica da aplicação com LLMs reais."""
from langgraph.graph import StateGraph, START, END

import config
from graph.state import EstadoQuestao
from graph.router import decide_proximo


def build_workflow(gerador_node, avaliador_node, organizador_node):
    """Monta e compila o grafo a partir das funções-nó injetadas."""
    g = StateGraph(EstadoQuestao)
    g.add_node("gerador", gerador_node)
    g.add_node("avaliador", avaliador_node)
    g.add_node("organizador", organizador_node)

    g.add_edge(START, "gerador")
    g.add_edge("gerador", "avaliador")
    g.add_conditional_edges(
        "avaliador",
        decide_proximo,
        {"gerador": "gerador", "organizador": "organizador"},
    )
    g.add_edge("organizador", END)
    return g.compile()


def create_app():
    """Cria a aplicação com os agentes reais (Ollama). Usada pela interface."""
    # Imports locais para manter build_workflow testável sem dependências de rede.
    from agents.llm_factory import make_llm
    from agents.schemas import Questao, Avaliacao, Classificacao
    from agents.gerador import make_gerador_node
    from agents.avaliador import make_avaliador_node
    from agents.organizador import make_organizador_node
    from bncc.loader import load_habilidades, format_habilidades

    gen_llm = make_llm(config.GENERATOR_MODEL, config.GENERATOR_TEMPERATURE)
    eval_llm = make_llm(config.EVALUATOR_MODEL, config.EVALUATOR_TEMPERATURE)
    org_llm = make_llm(config.ORGANIZER_MODEL, config.ORGANIZER_TEMPERATURE)

    habilidades_texto = format_habilidades(load_habilidades(config.BNCC_DATA_PATH))

    gerador = make_gerador_node(gen_llm.with_structured_output(Questao))
    avaliador = make_avaliador_node(eval_llm.with_structured_output(Avaliacao))
    organizador = make_organizador_node(
        org_llm.with_structured_output(Classificacao), habilidades_texto
    )
    return build_workflow(gerador, avaliador, organizador)
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_workflow.py -v`
Expected: PASS (3 testes)

- [ ] **Step 5: Rodar a suíte completa**

Run: `python -m pytest -v`
Expected: PASS — todos os testes das Tasks 2–10.

- [ ] **Step 6: Commit**

```bash
git add graph/workflow.py tests/test_workflow.py
git commit -m "feat: montagem do grafo LangGraph e fábrica da aplicação"
```

---

### Task 11: Interface Streamlit

**Files:**
- Create: `app.py`

**Nota:** a interface não tem teste unitário (Streamlit é difícil de testar isoladamente); ela é validada pelo smoke test manual da Task 12. Toda a lógica testável já está coberta nas Tasks 2–10.

- [ ] **Step 1: Implementar `app.py`**

```python
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


# Rótulos de progresso por nó do grafo
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
    except Exception as e:  # falha de conexão com Ollama ou modelo ausente
        st.error(
            "Não foi possível executar os agentes. Verifique se o Ollama está "
            f"rodando e se o modelo foi baixado (`ollama pull {config.GENERATOR_MODEL}`).\n\n"
            f"Detalhe técnico: {e}"
        )
        st.stop()

    # estado_final acumulou os updates; recombina com o tema para exibição
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
```

- [ ] **Step 2: Verificar que o app importa sem erro de sintaxe**

Run: `python -c "import ast; ast.parse(open('app.py', encoding='utf-8').read()); print('OK')"`
Expected: imprime `OK`

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: interface Streamlit com progresso por agente"
```

---

### Task 12: README e smoke test manual com Ollama

**Files:**
- Create: `README.md`

- [ ] **Step 1: Criar `README.md`**

```markdown
# SMA — Geração e Validação de Questões Educacionais

Sistema Multiagente (LangGraph) que gera questões de múltipla escolha de
Matemática para o Ensino Médio, alinhadas à BNCC. Agentes: **Gerador →
Avaliador → Organizador**, com loop de retry por qualidade (até 3 tentativas).

## Pré-requisitos

1. Python 3.11+
2. [Ollama](https://ollama.com) instalado e rodando
3. Modelo baixado:
   ```
   ollama pull qwen2.5:7b
   ```

## Instalação

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env   # ajuste se quiser trocar modelos
```

## Executar

```powershell
streamlit run app.py
```

## Testes

```powershell
python -m pytest -v
```

## Configuração

Edite `.env` para trocar os modelos por agente. Para usar um modelo mais
potente no Avaliador (recomendado para melhor qualidade):

```
EVALUATOR_MODEL=qwen2.5:14b
```

## Arquitetura

```
[entrada] → [gerador] → [avaliador] → (aprovada?) → [organizador] → [saída]
                ↑___________(reprovada, tentativas < 3)
```
```

- [ ] **Step 2: Smoke test manual (requer Ollama rodando)**

Pré-condição: `ollama serve` ativo e `ollama pull qwen2.5:7b` concluído.

Run: `streamlit run app.py`

Checklist de verificação no navegador:
1. [ ] A página abre com o título e o campo de entrada.
2. [ ] Clicar em "Funções do 2º grau" e gerar → aparece o progresso por agente (Gerando → Avaliando → Classificando).
3. [ ] A questão exibida tem enunciado e 4 alternativas (A–D).
4. [ ] O expander "Ver gabarito e explicação" mostra uma das letras A–D e um texto.
5. [ ] Aparece um código BNCC (EM13MAT*) com descrição.
6. [ ] Digitar `EM13MAT507` e gerar → produz uma questão coerente com probabilidade/contagem.
7. [ ] Parar o Ollama (`ollama stop` ou encerrar o serviço) e gerar → aparece a mensagem de erro amigável com instrução de `ollama pull`.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: README com instruções de uso e smoke test"
```

---

## Self-Review (preenchido)

**1. Cobertura da spec:**
- Stack (Python/LangGraph/Streamlit/Ollama/Qwen) → Tasks 1, 5, 10, 11 ✓
- Agente Gerador (temp 0.7, retry com feedback) → Task 6 + config ✓
- Agente Avaliador (temp 0.1, quality_passed) → Task 7 ✓
- Agente Organizador (temp 0.1, BNCC) → Tasks 4, 8 ✓
- Estado compartilhado → Task 3 ✓
- Fluxo LangGraph + loop + condição de saída (≥3) → Tasks 9, 10 ✓
- Modelo do Avaliador configurável via env → config + .env.example (Task 1) ✓
- Interface Streamlit (entrada/progresso/resultado, exemplos, gabarito, badge, aviso) → Task 11 ✓
- Entrada por tema livre OU código BNCC → Task 11 (mesmo campo) ✓
- Organizador classifica independente do input → Task 8 (classifica pelo conteúdo) ✓
- Tratamento de erros (Ollama indisponível, modelo ausente, limite de tentativas) → Tasks 9, 11 ✓
- Temperatura dual (melhoria da pesquisa) → config (Task 1) ✓

**2. Placeholders:** nenhum "TBD/TODO" em passos de implementação. Os dados BNCC são um subconjunto real e funcional, com nota para expansão futura — não bloqueia a execução.

**3. Consistência de tipos:** `make_*_node(structured_llm)` e `build_*_messages(...)` consistentes entre Tasks 6–8; nós retornam updates parciais com as chaves de `EstadoQuestao` (Task 3); `decide_proximo` (Task 9) lê `quality_passed`/`tentativas` e é usado em `build_workflow` (Task 10) com o mesmo path_map.

**Observação sobre o aviso de limite:** não há campo separado no estado; o aviso é derivado em `app.py` como `not quality_passed` (se chegou ao Organizador sem aprovação, foi por limite). Decisão intencional para manter o estado mínimo.

**Nota de troubleshooting (saída estruturada):** se um modelo pequeno falhar em produzir a saída estruturada via tool-calling, alterar as chamadas para `.with_structured_output(Schema, method="json_schema")` em `create_app` (Task 10).
