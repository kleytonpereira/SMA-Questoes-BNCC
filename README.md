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

## Pipeline de agentes (precisão)

`gerador → validador_regras → verificador → avaliador → avaliador_final → organizador`

- **validador_regras** — checagem determinística de item-writing flaws (sem custo de tokens): gabarito válido, alternativas não-vazias/duplicadas, sem "todas/nenhuma das anteriores", e sem pista de tamanho na alternativa correta.
- **verificador** — auto-consistência: re-resolve o problema N vezes (voto majoritário) e compara com o gabarito proposto.
- **avaliador** — revisão chain-of-thought (modelo regular).
- **avaliador_final** — segunda opinião obrigatória com modelo mais forte.
- **organizador** — classificação na habilidade BNCC.

Falha em qualquer camada antes do organizador devolve a questão ao gerador, respeitando `MAX_TENTATIVAS`.

Variáveis relevantes no `.env`: `VERIFIER_SAMPLES` (nº de re-soluções), `VERIFIER_TEMPERATURE`, `REGRA_TERMOS_ABSOLUTOS`.

### Fundamentação
- Generating AI Literacy MCQs: A Multi-Agent LLM Approach (arXiv 2412.00970)
- ReQUESTA: Hybrid Agentic Framework for MCQ Generation
- When AIs Judge AIs: Agent-as-a-Judge (arXiv 2508.02994)
