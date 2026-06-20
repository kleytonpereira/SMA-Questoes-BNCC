# Precisão para Modelos 4B — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aumentar a precisão do SMA com modelos pequenos (3-4B) adicionando duas camadas de validação (regras determinísticas + auto-consistência numérica) e ajustando prompts.

**Architecture:** Pipeline em camadas, barato → caro: `gerador → validador_regras (Python) → verificador (auto-consistência) → avaliador (LLM CoT) → avaliador_final (modelo forte) → organizador`. Falha em qualquer camada antes do organizador devolve ao gerador (respeitando `MAX_TENTATIVAS`).

**Tech Stack:** Python 3.14, LangGraph, langchain-ollama, Pydantic v2, pytest.

**Comando de teste padrão:** `C:\Users\klues\.venvs\SMA-Questoes\Scripts\python.exe -m pytest`

---

### Task 1: Config e schema `Resolucao`

**Files:**
- Modify: `config.py`
- Modify: `agents/schemas.py`
- Test: `tests/test_schemas.py`

- [ ] **Step 1: Escrever teste falhando para o schema `Resolucao`**

Adicionar em `tests/test_schemas.py`:

```python
def test_resolucao_valida():
    from agents.schemas import Resolucao
    r = Resolucao(alternativa="B")
    assert r.alternativa == "B"

def test_resolucao_rejeita_letra_invalida():
    import pytest
    from pydantic import ValidationError
    from agents.schemas import Resolucao
    with pytest.raises(ValidationError):
        Resolucao(alternativa="Z")
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `C:\Users\klues\.venvs\SMA-Questoes\Scripts\python.exe -m pytest tests/test_schemas.py -k resolucao -v`
Expected: FAIL com `ImportError` / `cannot import name 'Resolucao'`.

- [ ] **Step 3: Implementar o schema `Resolucao`**

Em `agents/schemas.py`, após a classe `Classificacao`:

```python
class Resolucao(BaseModel):
    alternativa: Literal["A", "B", "C", "D"] = Field(
        description="Letra da única alternativa correta após resolver o problema"
    )
```

- [ ] **Step 4: Adicionar variáveis de config**

Em `config.py`, antes da linha `BNCC_DATA_PATH = ...`:

```python
# Auto-consistência numérica (agente verificador)
VERIFIER_SAMPLES = int(os.getenv("VERIFIER_SAMPLES", "3"))
VERIFIER_TEMPERATURE = float(os.getenv("VERIFIER_TEMPERATURE", "0.7"))

# Regra opcional de termos absolutos no validador de regras (desligada por padrão)
REGRA_TERMOS_ABSOLUTOS = os.getenv("REGRA_TERMOS_ABSOLUTOS", "false").lower() == "true"
```

- [ ] **Step 5: Rodar o teste e confirmar que passa**

Run: `C:\Users\klues\.venvs\SMA-Questoes\Scripts\python.exe -m pytest tests/test_schemas.py -k resolucao -v`
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
git add config.py agents/schemas.py tests/test_schemas.py
git commit -m "feat: schema Resolucao e config de verificador/regras"
```

---

### Task 2: Agente `validador_regras` (determinístico, sem LLM)

**Files:**
- Create: `agents/validador_regras.py`
- Test: `tests/test_validador_regras.py`

- [ ] **Step 1: Escrever os testes falhando**

Criar `tests/test_validador_regras.py`:

```python
from agents.validador_regras import validar_regras, make_validador_regras_node

QUESTAO_OK = {
    "enunciado": "Qual o valor de 2+2?",
    "alternativa_a": "3", "alternativa_b": "4",
    "alternativa_c": "5", "alternativa_d": "6",
    "gabarito": "B", "explicacao": "2+2=4.",
}

def test_questao_valida_passa():
    passou, motivo = validar_regras(QUESTAO_OK)
    assert passou is True
    assert motivo == ""

def test_gabarito_invalido_reprova():
    q = {**QUESTAO_OK, "gabarito": "Z"}
    passou, motivo = validar_regras(q)
    assert passou is False
    assert "Gabarito" in motivo

def test_alternativa_vazia_reprova():
    q = {**QUESTAO_OK, "alternativa_c": "   "}
    passou, motivo = validar_regras(q)
    assert passou is False
    assert "vazia" in motivo.lower()

def test_alternativas_duplicadas_reprova():
    q = {**QUESTAO_OK, "alternativa_a": "4"}  # igual à B
    passou, motivo = validar_regras(q)
    assert passou is False
    assert "duplicad" in motivo.lower()

def test_todas_as_anteriores_reprova():
    q = {**QUESTAO_OK, "alternativa_d": "Todas as anteriores"}
    passou, motivo = validar_regras(q)
    assert passou is False
    assert "anteriores" in motivo.lower()

def test_correta_muito_mais_longa_reprova():
    q = {
        "enunciado": "Pergunta?",
        "alternativa_a": "x", "alternativa_b": "y",
        "alternativa_c": "Esta alternativa correta é deliberadamente muito mais longa que as outras todas",
        "alternativa_d": "z",
        "gabarito": "C", "explicacao": "...",
    }
    passou, motivo = validar_regras(q)
    assert passou is False
    assert "longa" in motivo.lower()

def test_termos_absolutos_desligado_por_padrao():
    q = {**QUESTAO_OK, "enunciado": "O resultado é sempre 4?"}
    passou, _ = validar_regras(q)
    assert passou is True

def test_termos_absolutos_ligado_reprova():
    q = {**QUESTAO_OK, "enunciado": "O resultado é sempre 4?"}
    passou, motivo = validar_regras(q, checar_termos_absolutos=True)
    assert passou is False
    assert "absoluto" in motivo.lower()

def test_node_seta_regras_passed_true():
    node = make_validador_regras_node()
    update = node({"questao": QUESTAO_OK})
    assert update["regras_passed"] is True
    assert update["motivo_rejeicao"] == ""

def test_node_seta_regras_passed_false_com_motivo():
    node = make_validador_regras_node()
    q = {**QUESTAO_OK, "gabarito": "Z"}
    update = node({"questao": q})
    assert update["regras_passed"] is False
    assert update["motivo_rejeicao"] != ""
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `C:\Users\klues\.venvs\SMA-Questoes\Scripts\python.exe -m pytest tests/test_validador_regras.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'agents.validador_regras'`.

- [ ] **Step 3: Implementar `agents/validador_regras.py`**

```python
"""Agente determinístico: checa falhas estruturais (item-writing flaws) sem LLM."""
import config

_EXPRESSOES_PROIBIDAS = (
    "todas as anteriores",
    "nenhuma das anteriores",
    "todas as alternativas",
    "n.d.a",
)
_TERMOS_ABSOLUTOS = ("sempre", "nunca", "jamais", "todo ", "toda ")


def _alternativas(questao: dict) -> dict:
    return {
        "A": questao.get("alternativa_a", ""),
        "B": questao.get("alternativa_b", ""),
        "C": questao.get("alternativa_c", ""),
        "D": questao.get("alternativa_d", ""),
    }


def validar_regras(questao: dict, checar_termos_absolutos: bool = False) -> tuple[bool, str]:
    """Retorna (passou, motivo). Motivo vazio quando passou."""
    alternativas = _alternativas(questao)

    # Regra 1: gabarito válido
    gabarito = questao.get("gabarito")
    if gabarito not in {"A", "B", "C", "D"}:
        return False, f"Gabarito inválido: {gabarito!r} (esperado A, B, C ou D)."

    # Regra 2: alternativa vazia
    for letra, texto in alternativas.items():
        if not texto or not texto.strip():
            return False, f"Alternativa {letra} está vazia."

    # Regra 3: alternativas duplicadas
    normalizadas = [t.strip().lower() for t in alternativas.values()]
    if len(set(normalizadas)) < len(normalizadas):
        return False, "Há alternativas duplicadas."

    # Regra 4: 'todas/nenhuma das anteriores'
    for letra, texto in alternativas.items():
        baixo = texto.strip().lower()
        if any(expr in baixo for expr in _EXPRESSOES_PROIBIDAS):
            return False, f"Alternativa {letra} usa expressão proibida (ex.: 'todas as anteriores')."

    # Regra 5: alternativa correta muito mais longa (pista de tamanho)
    correta_len = len(alternativas[gabarito].strip())
    outras = [len(alternativas[l].strip()) for l in alternativas if l != gabarito]
    media_outras = sum(outras) / len(outras) if outras else 0
    if media_outras > 0 and correta_len > 1.5 * media_outras:
        return False, "Alternativa correta é muito mais longa que as demais (pista de tamanho)."

    # Regra 6 (opcional): termos absolutos
    if checar_termos_absolutos:
        texto_completo = (
            questao.get("enunciado", "") + " " + " ".join(alternativas.values())
        ).lower()
        for termo in _TERMOS_ABSOLUTOS:
            if termo in texto_completo:
                return False, f"Uso de termo absoluto ('{termo.strip()}')."

    return True, ""


def make_validador_regras_node():
    """Devolve a função-nó do validador de regras."""
    def validador_regras_node(state: dict) -> dict:
        passou, motivo = validar_regras(
            state["questao"],
            checar_termos_absolutos=config.REGRA_TERMOS_ABSOLUTOS,
        )
        return {
            "regras_passed": passou,
            "motivo_rejeicao": "" if passou else motivo,
        }
    return validador_regras_node
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `C:\Users\klues\.venvs\SMA-Questoes\Scripts\python.exe -m pytest tests/test_validador_regras.py -v`
Expected: PASS (10 passed).

- [ ] **Step 5: Commit**

```bash
git add agents/validador_regras.py tests/test_validador_regras.py
git commit -m "feat: agente validador_regras (item-writing flaws, sem LLM)"
```

---

### Task 3: Agente `verificador` (auto-consistência numérica)

**Files:**
- Create: `agents/verificador.py`
- Test: `tests/test_verificador.py`

- [ ] **Step 1: Escrever os testes falhando**

Criar `tests/test_verificador.py`:

```python
from langchain_core.runnables import RunnableLambda
from agents.verificador import build_verificador_messages, make_verificador_node
from agents.schemas import Resolucao

QUESTAO = {
    "enunciado": "Quanto é 2+2?",
    "alternativa_a": "3", "alternativa_b": "4",
    "alternativa_c": "5", "alternativa_d": "6",
    "gabarito": "B", "explicacao": "2+2=4.",
}

def test_build_messages_inclui_alternativas_mas_nao_gabarito():
    msgs = build_verificador_messages(QUESTAO)
    conteudo = " ".join(m.content for m in msgs)
    assert "Quanto é 2+2?" in conteudo
    assert "B) 4" in conteudo
    # Não deve revelar qual é o gabarito
    assert "gabarito" not in conteudo.lower()

def test_maioria_concorda_com_gabarito_aprova():
    fake = RunnableLambda(lambda _: Resolucao(alternativa="B"))
    node = make_verificador_node(fake, n_samples=3)
    update = node({"questao": QUESTAO})
    assert update["quality_passed"] is True
    assert update["motivo_rejeicao"] == ""

def test_maioria_diverge_do_gabarito_reprova():
    fake = RunnableLambda(lambda _: Resolucao(alternativa="C"))
    node = make_verificador_node(fake, n_samples=3)
    update = node({"questao": QUESTAO})
    assert update["quality_passed"] is False
    assert "C" in update["motivo_rejeicao"]
    assert "B" in update["motivo_rejeicao"]

def test_voto_majoritario_com_empate_parcial():
    # Sequência B, C, B -> maioria B (concorda com gabarito)
    respostas = iter(["B", "C", "B"])
    fake = RunnableLambda(lambda _: Resolucao(alternativa=next(respostas)))
    node = make_verificador_node(fake, n_samples=3)
    update = node({"questao": QUESTAO})
    assert update["quality_passed"] is True
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `C:\Users\klues\.venvs\SMA-Questoes\Scripts\python.exe -m pytest tests/test_verificador.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'agents.verificador'`.

- [ ] **Step 3: Implementar `agents/verificador.py`**

```python
"""Agente verificador: auto-consistência numérica por voto majoritário."""
from collections import Counter
from langchain_core.messages import SystemMessage, HumanMessage
from agents.schemas import format_questao

SYSTEM_PROMPT = (
    "Você é um solucionador de problemas de Matemática do Ensino Médio. "
    "Resolva o problema apresentado passo a passo e escolha a ÚNICA alternativa correta "
    "entre A, B, C e D. Não confie em nenhuma indicação de resposta: calcule você mesmo."
)


def build_verificador_messages(questao: dict) -> list:
    """Mensagens que mostram enunciado e alternativas, SEM revelar o gabarito."""
    humano = (
        "Resolva o problema abaixo e responda apenas com a letra da alternativa correta.\n\n"
        f"{format_questao(questao)}"
    )
    return [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=humano)]


def make_verificador_node(structured_llm, n_samples: int):
    """Devolve a função-nó do verificador. Re-resolve n_samples vezes e vota."""
    def verificador_node(state: dict) -> dict:
        questao = state["questao"]
        msgs = build_verificador_messages(questao)
        votos = [structured_llm.invoke(msgs).alternativa for _ in range(n_samples)]
        vencedora, _ = Counter(votos).most_common(1)[0]
        gabarito = questao["gabarito"]
        if vencedora == gabarito:
            return {"quality_passed": True, "motivo_rejeicao": ""}
        return {
            "quality_passed": False,
            "motivo_rejeicao": (
                f"Auto-consistência divergiu: o solucionador escolheu '{vencedora}' "
                f"em {votos.count(vencedora)}/{n_samples} amostras, mas o gabarito informado "
                f"é '{gabarito}'. Revise o cálculo e o gabarito."
            ),
        }
    return verificador_node
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `C:\Users\klues\.venvs\SMA-Questoes\Scripts\python.exe -m pytest tests/test_verificador.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add agents/verificador.py tests/test_verificador.py
git commit -m "feat: agente verificador (auto-consistência por voto majoritário)"
```

---

### Task 4: Campo `regras_passed` no estado

**Files:**
- Modify: `graph/state.py`
- Test: `tests/test_state.py`

- [ ] **Step 1: Atualizar o teste de estado**

Em `tests/test_state.py`, garantir que o teste aceita o novo campo. Substituir o corpo do teste existente por:

```python
def test_estado_aceita_campos_esperados():
    from graph.state import EstadoQuestao
    estado: EstadoQuestao = {
        "tema": "funções",
        "tentativas": 0,
        "ciclos": 0,
        "regras_passed": False,
        "questao": {},
        "quality_passed": False,
        "motivo_rejeicao": "",
        "habilidade_bncc": "",
        "descricao_bncc": "",
    }
    assert estado["regras_passed"] is False
    assert estado["tema"] == "funções"
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `C:\Users\klues\.venvs\SMA-Questoes\Scripts\python.exe -m pytest tests/test_state.py -v`
Expected: FAIL (o `EstadoQuestao` ainda não tem `regras_passed`; o TypedDict não valida em runtime, então se passar, prossiga — o objetivo real é o Step 3).

- [ ] **Step 3: Adicionar o campo em `graph/state.py`**

```python
"""Estado compartilhado entre os nós do grafo LangGraph."""
from typing import TypedDict

class EstadoQuestao(TypedDict):
    tema: str
    tentativas: int
    ciclos: int
    regras_passed: bool
    questao: dict
    quality_passed: bool
    motivo_rejeicao: str
    habilidade_bncc: str
    descricao_bncc: str
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `C:\Users\klues\.venvs\SMA-Questoes\Scripts\python.exe -m pytest tests/test_state.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add graph/state.py tests/test_state.py
git commit -m "feat: campo regras_passed no estado"
```

---

### Task 5: Roteadores das novas camadas

**Files:**
- Modify: `graph/router.py`
- Test: `tests/test_router.py`

- [ ] **Step 1: Escrever os testes falhando**

Adicionar em `tests/test_router.py` (no topo, junto aos imports existentes):

```python
from graph.router import decide_apos_validador, decide_apos_verificador
```

E adicionar os testes ao final do arquivo:

```python
# --- decide_apos_validador ---

def test_validador_regras_ok_vai_para_verificador():
    assert decide_apos_validador({"regras_passed": True, "tentativas": 1}) == "verificador"

def test_validador_regras_falha_com_tentativas_volta_para_gerador():
    assert decide_apos_validador({"regras_passed": False, "tentativas": 1}) == "gerador"

def test_validador_regras_falha_no_limite_segue_para_verificador():
    assert decide_apos_validador({"regras_passed": False, "tentativas": 3}) == "verificador"

# --- decide_apos_verificador ---

def test_verificador_aprovado_vai_para_avaliador():
    assert decide_apos_verificador({"quality_passed": True, "tentativas": 1}) == "avaliador"

def test_verificador_reprovado_com_tentativas_volta_para_gerador():
    assert decide_apos_verificador({"quality_passed": False, "tentativas": 1}) == "gerador"

def test_verificador_reprovado_no_limite_segue_para_avaliador():
    assert decide_apos_verificador({"quality_passed": False, "tentativas": 3}) == "avaliador"
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `C:\Users\klues\.venvs\SMA-Questoes\Scripts\python.exe -m pytest tests/test_router.py -v`
Expected: FAIL com `ImportError: cannot import name 'decide_apos_validador'`.

- [ ] **Step 3: Adicionar os roteadores em `graph/router.py`**

Adicionar ao final do arquivo (mantendo `decide_apos_avaliador` e `decide_apos_avaliador_final` intactos):

```python
def decide_apos_validador(state: dict) -> Literal["gerador", "verificador"]:
    """Após o validador de regras:
    - Regras OK → verificador
    - Regras falharam e ainda há tentativas → gerador
    - Regras falharam e tentativas esgotadas → verificador (camadas seguintes julgam)
    """
    if state.get("regras_passed"):
        return "verificador"
    if state["tentativas"] >= config.MAX_TENTATIVAS:
        return "verificador"
    return "gerador"


def decide_apos_verificador(state: dict) -> Literal["gerador", "avaliador"]:
    """Após o verificador (auto-consistência):
    - Aprovado → avaliador
    - Reprovado e ainda há tentativas → gerador
    - Reprovado e tentativas esgotadas → avaliador
    """
    if state["quality_passed"]:
        return "avaliador"
    if state["tentativas"] >= config.MAX_TENTATIVAS:
        return "avaliador"
    return "gerador"
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `C:\Users\klues\.venvs\SMA-Questoes\Scripts\python.exe -m pytest tests/test_router.py -v`
Expected: PASS (todos os testes do router).

- [ ] **Step 5: Commit**

```bash
git add graph/router.py tests/test_router.py
git commit -m "feat: roteadores decide_apos_validador e decide_apos_verificador"
```

---

### Task 6: Wiring no workflow

**Files:**
- Modify: `graph/workflow.py`
- Test: `tests/test_workflow.py`

- [ ] **Step 1: Atualizar os testes do workflow**

Substituir TODO o conteúdo de `tests/test_workflow.py` por:

```python
from graph.workflow import build_workflow

BASE_STATE = {
    "tema": "funções",
    "tentativas": 0,
    "ciclos": 0,
    "regras_passed": False,
    "quality_passed": False,
    "motivo_rejeicao": "",
    "questao": {},
    "habilidade_bncc": "",
    "descricao_bncc": "",
}


def _make_app(gerador, validador, verificador, avaliador, avaliador_final, organizador):
    return build_workflow(gerador, validador, verificador, avaliador, avaliador_final, organizador)


def test_workflow_fluxo_feliz_passa_por_todas_as_camadas():
    ordem = []

    def gerador(state):
        ordem.append("gerador")
        return {"tentativas": state["tentativas"] + 1, "questao": {"gabarito": "A"}}
    def validador(state):
        ordem.append("validador")
        return {"regras_passed": True, "motivo_rejeicao": ""}
    def verificador(state):
        ordem.append("verificador")
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def avaliador(state):
        ordem.append("avaliador")
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def avaliador_final(state):
        ordem.append("avaliador_final")
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def organizador(state):
        ordem.append("organizador")
        return {"habilidade_bncc": "EM13MAT302", "descricao_bncc": "Funções"}

    app = _make_app(gerador, validador, verificador, avaliador, avaliador_final, organizador)
    final = app.invoke(BASE_STATE)
    assert ordem == ["gerador", "validador", "verificador", "avaliador", "avaliador_final", "organizador"]
    assert final["habilidade_bncc"] == "EM13MAT302"


def test_workflow_regras_falham_voltam_ao_gerador():
    chamadas = {"validador": 0}

    def gerador(state):
        return {"tentativas": state["tentativas"] + 1, "questao": {"gabarito": "A"}}
    def validador(state):
        chamadas["validador"] += 1
        if chamadas["validador"] == 1:
            return {"regras_passed": False, "motivo_rejeicao": "Alternativa vazia"}
        return {"regras_passed": True, "motivo_rejeicao": ""}
    def verificador(state):
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def avaliador(state):
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def avaliador_final(state):
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def organizador(state):
        return {"habilidade_bncc": "EM13MAT302", "descricao_bncc": "Funções"}

    app = _make_app(gerador, validador, verificador, avaliador, avaliador_final, organizador)
    final = app.invoke(BASE_STATE)
    assert chamadas["validador"] == 2
    assert final["tentativas"] == 2


def test_workflow_verificador_diverge_volta_ao_gerador():
    chamadas = {"verificador": 0}

    def gerador(state):
        return {"tentativas": state["tentativas"] + 1, "questao": {"gabarito": "A"}}
    def validador(state):
        return {"regras_passed": True, "motivo_rejeicao": ""}
    def verificador(state):
        chamadas["verificador"] += 1
        if chamadas["verificador"] == 1:
            return {"quality_passed": False, "motivo_rejeicao": "Divergência"}
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def avaliador(state):
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def avaliador_final(state):
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def organizador(state):
        return {"habilidade_bncc": "EM13MAT302", "descricao_bncc": "Funções"}

    app = _make_app(gerador, validador, verificador, avaliador, avaliador_final, organizador)
    final = app.invoke(BASE_STATE)
    assert chamadas["verificador"] == 2
    assert final["habilidade_bncc"] == "EM13MAT302"


def test_workflow_avaliador_aprovado_passa_pelo_avaliador_final():
    chamadas = {"avaliador_final": 0}

    def gerador(state):
        return {"tentativas": state["tentativas"] + 1, "questao": {"gabarito": "A"}}
    def validador(state):
        return {"regras_passed": True, "motivo_rejeicao": ""}
    def verificador(state):
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def avaliador(state):
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def avaliador_final(state):
        chamadas["avaliador_final"] += 1
        return {"quality_passed": True, "motivo_rejeicao": ""}
    def organizador(state):
        return {"habilidade_bncc": "EM13MAT302", "descricao_bncc": "Funções"}

    app = _make_app(gerador, validador, verificador, avaliador, avaliador_final, organizador)
    final = app.invoke(BASE_STATE)
    assert chamadas["avaliador_final"] == 1
    assert final["quality_passed"] is True
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `C:\Users\klues\.venvs\SMA-Questoes\Scripts\python.exe -m pytest tests/test_workflow.py -v`
Expected: FAIL (assinatura de `build_workflow` ainda tem 4 parâmetros).

- [ ] **Step 3: Reescrever `graph/workflow.py`**

```python
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
    from agents.llm_factory import make_llm
    from agents.schemas import Questao, Avaliacao, Classificacao, Resolucao
    from agents.gerador import make_gerador_node
    from agents.validador_regras import make_validador_regras_node
    from agents.verificador import make_verificador_node
    from agents.avaliador import make_avaliador_node, make_avaliador_final_node
    from agents.organizador import make_organizador_node
    from bncc.loader import load_habilidades, format_habilidades

    gen_llm = make_llm(config.GENERATOR_MODEL, config.GENERATOR_TEMPERATURE)
    eval_llm = make_llm(config.EVALUATOR_MODEL, config.EVALUATOR_TEMPERATURE)
    strong_eval_llm = make_llm(config.STRONG_EVALUATOR_MODEL, config.STRONG_EVALUATOR_TEMPERATURE)
    org_llm = make_llm(config.ORGANIZER_MODEL, config.ORGANIZER_TEMPERATURE)
    verif_llm = make_llm(config.GENERATOR_MODEL, config.VERIFIER_TEMPERATURE)

    habilidades_texto = format_habilidades(load_habilidades(config.BNCC_DATA_PATH))

    gerador = make_gerador_node(gen_llm.with_structured_output(Questao))
    validador_regras = make_validador_regras_node()
    verificador = make_verificador_node(
        verif_llm.with_structured_output(Resolucao), config.VERIFIER_SAMPLES
    )
    avaliador = make_avaliador_node(eval_llm.with_structured_output(Avaliacao))
    avaliador_final = make_avaliador_final_node(strong_eval_llm.with_structured_output(Avaliacao))
    organizador = make_organizador_node(
        org_llm.with_structured_output(Classificacao), habilidades_texto
    )
    return build_workflow(
        gerador, validador_regras, verificador, avaliador, avaliador_final, organizador
    )
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `C:\Users\klues\.venvs\SMA-Questoes\Scripts\python.exe -m pytest tests/test_workflow.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add graph/workflow.py tests/test_workflow.py
git commit -m "feat: integra validador_regras e verificador no grafo"
```

---

### Task 7: Prompts ajustados para modelos 4B

**Files:**
- Modify: `agents/gerador.py`
- Test: `tests/test_gerador.py` (apenas garantir que segue passando)

- [ ] **Step 1: Reescrever o `SYSTEM_PROMPT` do gerador com instruções diretas + few-shot**

Em `agents/gerador.py`, substituir a constante `SYSTEM_PROMPT` por:

```python
SYSTEM_PROMPT = (
    "Você é um professor de Matemática do Ensino Médio brasileiro. "
    "Crie UMA questão de múltipla escolha alinhada à BNCC, seguindo EXATAMENTE estas regras:\n"
    "1. Exatamente quatro alternativas: A, B, C e D.\n"
    "2. Apenas UMA alternativa correta.\n"
    "3. As três alternativas erradas devem ser plausíveis (erros comuns), nunca absurdas.\n"
    "4. As quatro alternativas devem ter tamanho parecido.\n"
    "5. NÃO use 'todas as anteriores' nem 'nenhuma das anteriores'.\n"
    "6. Antes de responder, RESOLVA o problema e confirme que o gabarito está correto.\n\n"
    "Exemplo de questão bem-formada:\n"
    "Enunciado: Qual é o valor de x na equação 2x + 6 = 14?\n"
    "A) 2\nB) 4\nC) 6\nD) 8\n"
    "Gabarito: B\n"
    "Explicação: 2x = 14 - 6 = 8, logo x = 4.\n\n"
    "Gere uma questão nesse mesmo padrão para o tema solicitado."
)
```

- [ ] **Step 2: Rodar os testes do gerador**

Run: `C:\Users\klues\.venvs\SMA-Questoes\Scripts\python.exe -m pytest tests/test_gerador.py -v`
Expected: PASS (os testes verificam mensagens e incremento de tentativas; a mudança de prompt não os quebra).

- [ ] **Step 3: Commit**

```bash
git add agents/gerador.py
git commit -m "feat: prompt do gerador com regras explícitas e few-shot (modelos 4B)"
```

---

### Task 8: Rótulos da UI e estado inicial

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Atualizar `estado_inicial` e `ROTULOS`**

Em `app.py`, na função `estado_inicial`, adicionar `"regras_passed": False,` logo após `"ciclos": 0,`:

```python
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
```

Substituir o dicionário `ROTULOS` por:

```python
ROTULOS = {
    "gerador": "✍️ Gerando questão...",
    "validador_regras": "📋 Checando regras estruturais...",
    "verificador": "🔢 Verificando consistência numérica...",
    "avaliador": "🔍 Avaliando qualidade...",
    "avaliador_final": "🧠 Avaliação final (modelo forte)...",
    "organizador": "🏷️ Classificando pela BNCC...",
}
```

- [ ] **Step 2: Verificar que o app importa sem erro**

Run: `C:\Users\klues\.venvs\SMA-Questoes\Scripts\python.exe -c "import ast; ast.parse(open('app.py', encoding='utf-8').read()); print('ok')"`
Expected: `ok`.

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: rótulos das novas camadas e regras_passed no estado inicial"
```

---

### Task 9: Suíte completa, README e `.env.example`

**Files:**
- Modify: `README.md`
- Modify: `.env.example` (se existir; senão criar)

- [ ] **Step 1: Rodar a suíte completa**

Run: `C:\Users\klues\.venvs\SMA-Questoes\Scripts\python.exe -m pytest -v`
Expected: PASS (todos os testes verdes).

- [ ] **Step 2: Documentar a nova arquitetura no `README.md`**

Adicionar uma seção descrevendo o pipeline de 6 nós e citando os papers:

```markdown
## Pipeline de agentes (precisão)

`gerador → validador_regras → verificador → avaliador → avaliador_final → organizador`

- **validador_regras** — checagem determinística de item-writing flaws (sem custo de tokens).
- **verificador** — auto-consistência: re-resolve o problema N vezes e compara por voto majoritário.
- **avaliador** — revisão chain-of-thought.
- **avaliador_final** — segunda opinião com modelo mais forte.

Variáveis relevantes no `.env`: `VERIFIER_SAMPLES`, `VERIFIER_TEMPERATURE`, `REGRA_TERMOS_ABSOLUTOS`.

### Fundamentação
- Generating AI Literacy MCQs: A Multi-Agent LLM Approach (arXiv 2412.00970)
- ReQUESTA: Hybrid Agentic Framework for MCQ Generation
- When AIs Judge AIs: Agent-as-a-Judge (arXiv 2508.02994)
```

- [ ] **Step 3: Atualizar `.env.example`**

Adicionar (criar o arquivo se não existir, sem chaves reais):

```
GENERATOR_MODEL=qwen3:4b
EVALUATOR_MODEL=qwen3:4b
STRONG_EVALUATOR_MODEL=gemma4:12b
ORGANIZER_MODEL=qwen3:4b
VERIFIER_SAMPLES=3
VERIFIER_TEMPERATURE=0.7
REGRA_TERMOS_ABSOLUTOS=false
```

- [ ] **Step 4: Commit**

```bash
git add README.md .env.example
git commit -m "docs: pipeline de precisão e variáveis de ambiente"
```

---

## Notas de execução

- O `verificador` faz `VERIFIER_SAMPLES` chamadas por questão. Para economizar tokens durante o estudo comparativo, reduza para 1 (desliga a auto-consistência) ou aumente para 5 (mais robusto).
- A regra de "alternativa mais longa" usa margem de 1.5×; se gerar muitos falsos positivos com modelos 4B, ajuste em `agents/validador_regras.py`.
- Comparação entre modelos: troque `GENERATOR_MODEL`/`EVALUATOR_MODEL`/`ORGANIZER_MODEL` no `.env` e observe tempo/tokens/aprovação no LangSmith.
