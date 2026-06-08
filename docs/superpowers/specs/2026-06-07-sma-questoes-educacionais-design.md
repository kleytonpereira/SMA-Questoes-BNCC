# Design: Sistema Multiagente para Geração e Validação de Questões Educacionais

**Data:** 2026-06-07  
**Equipe:** Milena de Almeida Chaves, Kleyton Klueriston Ferreira Pereira, Miqueias Bento da Silva  
**Disciplina:** Sistemas Multiagentes — UFC  

---

## 1. Visão Geral

Sistema Multiagente (SMA) em Python que gera questões de múltipla escolha de Matemática para o Ensino Médio, alinhadas à BNCC. O usuário informa um tema livre ou um código de habilidade BNCC; o sistema retorna a questão, gabarito e classificação curricular.

**Delimitação de escopo:**
- Tipo de questão: múltipla escolha (4 alternativas A-D)
- Disciplina: Matemática
- Nível: Ensino Médio
- Referencial curricular: BNCC (habilidades EM13MAT\*)

---

## 2. Stack Tecnológica

| Componente | Tecnologia |
|---|---|
| Linguagem | Python 3.11+ |
| Orquestração dos agentes | LangGraph |
| Interface de usuário | Streamlit |
| Servidor de modelos local | Ollama |
| Modelo padrão | Qwen 2.5 7B (`qwen2.5:7b`) |
| Modelo do Avaliador (configurável) | `EVALUATOR_MODEL` via `.env` |

O modelo do Agente Avaliador é configurável via variável de ambiente `EVALUATOR_MODEL`. Padrão: `qwen2.5:7b`. Pode ser substituído por modelos via API (ex: `claude-3-5-haiku`) ou modelos Ollama maiores sem alteração de código.

---

## 3. Arquitetura dos Agentes

### 3.1 Agente Gerador

**Responsabilidade:** Criar enunciado, 4 alternativas e gabarito com explicação.

**Temperatura:** `0.7` (criatividade necessária para variação nas questões)

**Entrada:**
```json
{
  "tema": "funções do 2º grau",
  "motivo_rejeicao": "Alternativa C está matematicamente incorreta" // null na 1ª tentativa
}
```

**Saída:**
```json
{
  "enunciado": "...",
  "alternativas": { "A": "...", "B": "...", "C": "...", "D": "..." },
  "gabarito": "B",
  "explicacao": "..."
}
```

**Comportamento em retry:** Na 2ª e 3ª tentativa, o motivo de rejeição do Avaliador é injetado no prompt para que o Gerador corrija o problema específico.

---

### 3.2 Agente Avaliador

**Responsabilidade:** Verificar corretude matemática, coerência pedagógica e adequação ao EM.

**Temperatura:** `0.1` (análise precisa, sem variação)

**Critérios de avaliação:**
- Gabarito correto e único
- Alternativas plausíveis (distractors não óbvios)
- Linguagem adequada ao Ensino Médio
- Questão alinhada ao tema solicitado
- Ausência de ambiguidade no enunciado

**Entrada:** questão gerada + tema original

**Saída:**
```json
{
  "quality_passed": true,
  "motivo": "Aprovada" // ou descrição do problema se rejeitada
}
```

---

### 3.3 Agente Organizador

**Responsabilidade:** Classificar a questão aprovada com o código BNCC mais adequado, sempre com base no conteúdo da questão gerada (não no input do usuário).

**Temperatura:** `0.1` (classificação exata)

**Fonte de dados:** arquivo estático `data/bncc_matematica.json` com todas as habilidades EM13MAT\* do Ensino Médio.

**Entrada:** questão aprovada + tema original do usuário

**Saída:**
```json
{
  "codigo_bncc": "EM13MAT302",
  "descricao_habilidade": "Construir modelos empregando as funções quadráticas..."
}
```

**Comportamento quando o usuário informou código BNCC:** o Organizador ainda classifica de forma independente. Se o código classificado divergir do solicitado, a interface exibe ambos — isso é pedagogicamente interessante e demonstra a capacidade de análise do sistema.

---

## 4. Fluxo LangGraph

### 4.1 Estado Compartilhado

```python
class EstadoQuestao(TypedDict):
    tema: str                  # entrada do usuário
    tentativas: int            # contador de retry (inicia em 0)
    questao: dict              # saída do Agente Gerador
    quality_passed: bool       # flag de aprovação do Avaliador
    motivo_rejeicao: str       # feedback do Avaliador para o Gerador
    habilidade_bncc: str       # código classificado pelo Organizador
    descricao_bncc: str        # descrição da habilidade
```

### 4.2 Grafo

```
[entrada]
    ↓
[agente_gerador]
    ↓
[agente_avaliador]
    ↓
[roteador] ─── quality_passed=True ──→ [agente_organizador] → [saída]
    │
    └── quality_passed=False AND tentativas < 3 ──→ [agente_gerador]
    │
    └── quality_passed=False AND tentativas ≥ 3 ──→ [agente_organizador] (com aviso)
```

### 4.3 Condição de Saída do Loop

O roteador verifica em ordem:
1. `quality_passed == True` → avança para Organizador
2. `tentativas >= 3` → avança para Organizador com flag `aviso_max_tentativas=True`
3. Caso contrário → volta ao Gerador, incrementa `tentativas`

---

## 5. Estrutura de Arquivos

```
sma-questoes/
├── app.py                        # Interface Streamlit
├── agents/
│   ├── gerador.py                # Agente Gerador
│   ├── avaliador.py              # Agente Avaliador
│   └── organizador.py            # Agente Organizador
├── graph/
│   └── workflow.py               # Grafo LangGraph, estado e roteador
├── data/
│   └── bncc_matematica.json      # Habilidades EM13MAT* (estático)
├── config.py                     # Parâmetros e variáveis de ambiente
├── .env.example                  # Exemplo de configuração
└── requirements.txt
```

---

## 6. Interface Streamlit

Tela única com três áreas:

**Entrada**
- Campo de texto: *"Digite o tema ou código BNCC (ex: 'funções do 2º grau' ou 'EM13MAT302')"*
- Chips de exemplo clicáveis para facilitar testes
- Botão **Gerar Questão**

**Progresso** (visível durante geração)
- Indicador do agente em execução: `Gerando...`, `Avaliando...`, `Classificando...`
- Número da tentativa atual quando houver retry

**Resultado**
- Enunciado da questão
- Alternativas A, B, C, D
- Botão **Ver Gabarito** (revela gabarito + explicação)
- Código BNCC + descrição da habilidade
- Badge de tentativas usadas (ex: `✓ Aprovada na 2ª tentativa`)
- Aviso quando atingido limite de tentativas sem aprovação

---

## 7. Configuração

**`.env.example`:**
```env
# Modelo para o Agente Avaliador (padrão: qwen2.5:7b via Ollama)
# Para usar Claude: EVALUATOR_MODEL=claude-3-5-haiku-20241022
# Para usar modelo maior local: EVALUATOR_MODEL=llama3.1:70b
EVALUATOR_MODEL=qwen2.5:7b

# URL do servidor Ollama
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 8. Tratamento de Erros

| Cenário | Comportamento |
|---|---|
| Ollama não disponível | Mensagem clara na interface com instruções |
| Modelo não encontrado no Ollama | Mensagem com comando `ollama pull` |
| 3 tentativas sem aprovação | Entrega questão com badge de aviso amarelo |
| Código BNCC inválido | Agente Organizador tenta o mais próximo; informa incerteza |
| Resposta malformada do LLM | Retry automático (até 2x) via LangGraph error handling |

---

## 9. Evolução Futura (Fora do Escopo Atual)

**Opção C — Reescrita Guiada:** Em vez de rejeitar a questão inteira, o Avaliador envia feedback estruturado por campo (enunciado, alternativa específica, gabarito) e o Gerador reescreve apenas o trecho problemático. Requer modelo mais capaz no Avaliador para feedback preciso.

**Multi-disciplinas:** Estender `bncc_matematica.json` para outras áreas da BNCC.

**Histórico de questões:** Persistência local em SQLite para evitar duplicatas.
