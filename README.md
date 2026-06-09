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
