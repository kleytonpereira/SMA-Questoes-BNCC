# Design: Aumento de precisão para modelos 4B

**Data:** 2026-06-21
**Contexto:** SMA de geração e validação de questões BNCC (Matemática, Ensino Médio).

## Problema

O sistema será avaliado com modelos pequenos (3-4B: `qwen3:4b`, `gemma3:4b`, `phi4-mini`, `llama3.2:3b`)
para um estudo comparativo. Modelos dessa faixa cometem mais erros de **estrutura** (alternativas
malformadas, falhas de item-writing) e de **cálculo** do que modelos 7B+. É preciso aumentar a
precisão sem depender de um modelo grande.

Fundamentação: "Generating AI Literacy MCQs: A Multi-Agent LLM Approach" (arXiv 2412.00970),
ReQUESTA (framework híbrido LLM + regras, 95% de concordância com especialistas) e
"Agent-as-a-Judge" (arXiv 2508.02994).

## Abordagem escolhida: Pipeline em camadas (defesa em profundidade)

Cada melhoria é um **agente/nó distinto**, na ordem barato → caro (filtra antes de gastar tokens):

```
gerador
  → validador_regras   (Python puro, 0 tokens)
  → verificador        (auto-consistência, N re-soluções com voto majoritário)
  → avaliador          (qwen3:8b, chain-of-thought)
  → avaliador_final    (modelo forte; segunda opinião obrigatória)
  → organizador        (classificação BNCC)
```

## Componentes

### 1. Agente `validador_regras` (determinístico, sem LLM)

- **Arquivo:** `agents/validador_regras.py`
- **Entrada:** `state["questao"]` (dict com enunciado, alternativas A-D, gabarito).
- **Função:** `validar_regras(questao: dict) -> tuple[bool, str]` — retorna `(passou, motivo)`.
- **Regras (item-writing flaws):**
  1. Gabarito fora de {A, B, C, D}.
  2. Alguma alternativa vazia ou só espaços.
  3. Alternativas duplicadas (comparação case-insensitive, sem espaços).
  4. Presença de "todas as anteriores" / "nenhuma das anteriores".
  5. Alternativa correta é a mais longa por margem grande (pista de tamanho): correta com
     comprimento > 1.5× a média das demais.
  6. (Opcional, **desligada por padrão**) Termos absolutos ("sempre", "nunca", "jamais").
     Em matemática termos absolutos costumam ser legítimos ("função sempre crescente"),
     então fica atrás da flag `REGRA_TERMOS_ABSOLUTOS` para evitar falsos positivos.
- **Nó:** `make_validador_regras_node()` → seta `regras_passed: bool` e, se falhar,
  `motivo_rejeicao`.
- **Sem dependência de LLM** → testável diretamente, sem fakes.

### 2. Agente `verificador` (auto-consistência numérica)

- **Arquivo:** `agents/verificador.py`
- **Schema novo:** `Resolucao { alternativa: Literal["A","B","C","D"] }` em `agents/schemas.py`.
- **Função:** re-resolve o problema `VERIFIER_SAMPLES` vezes (default 3, lido do `.env`),
  usando temperatura > 0 para diversidade, **sem ver o gabarito proposto**. Voto majoritário.
- **Decisão:** se a alternativa majoritária ≠ `questao["gabarito"]` → `quality_passed=False`,
  `motivo_rejeicao` explica a divergência → volta ao gerador.
- **Nó:** `make_verificador_node(structured_llm, n_samples)`.
- Usa o mesmo modelo do gerador (auto-consistência = mesmo modelo votando).

### 3. Prompts ajustados para 4B

- `agents/gerador.py` e `agents/avaliador.py`: instruções mais explícitas e diretas, com
  **um exemplo few-shot** de questão bem-formada. Modelos 4B seguem instruções complexas pior;
  exemplos concretos reduzem desvio de formato.

## Estado (`graph/state.py`)

Adicionar:
- `regras_passed: bool`

Mantém `tentativas` e `ciclos` existentes. Cada retorno ao gerador (por qualquer camada) conta
tentativa, com o mesmo teto `MAX_TENTATIVAS`.

## Roteamento (`graph/router.py`)

Novos roteadores, todos respeitando `MAX_TENTATIVAS` para evitar loop infinito:

- `decide_apos_validador(state)`:
  - `regras_passed` → `verificador`
  - reprovado e `tentativas < MAX_TENTATIVAS` → `gerador`
  - reprovado e tentativas esgotadas → `verificador` (deixa as camadas seguintes julgarem)
- `decide_apos_verificador(state)`:
  - `quality_passed` → `avaliador`
  - reprovado e `tentativas < MAX_TENTATIVAS` → `gerador`
  - reprovado e tentativas esgotadas → `avaliador`
- `decide_apos_avaliador` e `decide_apos_avaliador_final`: mantidos como já estão.

## Workflow (`graph/workflow.py`)

Adicionar nós `validador_regras` e `verificador`. Arestas:
`START → gerador → validador_regras → (verificador | gerador)`,
`verificador → (avaliador | gerador)`, e o restante inalterado.
`create_app()` injeta o `verificador` usando um LLM do modelo gerador com `Resolucao`.

## Config (`config.py` / `.env`)

- `VERIFIER_SAMPLES` (default 3) — nº de re-soluções na auto-consistência.
- `VERIFIER_TEMPERATURE` (default 0.7) — temperatura das re-soluções.

## Testes

- `tests/test_validador_regras.py`: cada regra IWF isolada (sem LLM).
- `tests/test_verificador.py`: voto majoritário concorda/diverge do gabarito (LLM fake).
- `tests/test_router.py`: novos roteadores (aprovado/reprovado/limite).
- `tests/test_workflow.py`: fluxo completo com fakes passando por todas as camadas.

## Fora de escopo (YAGNI)

- Não paralelizar as camadas (sequencial é suficiente e mais barato).
- Não adicionar personas múltiplas de avaliador agora.
- Não mexer na interface Streamlit além de já refletir os novos rótulos de nó.
