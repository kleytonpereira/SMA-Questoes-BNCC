"""Configuração central do SMA. Lê variáveis de ambiente do .env."""
import os
from pathlib import Path
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).parent
load_dotenv(_PROJECT_ROOT / ".env")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

GENERATOR_MODEL = os.getenv("GENERATOR_MODEL", "qwen2.5:7b")
EVALUATOR_MODEL = os.getenv("EVALUATOR_MODEL", "qwen3:8b")
STRONG_EVALUATOR_MODEL = os.getenv("STRONG_EVALUATOR_MODEL", "gemma4:12b")
ORGANIZER_MODEL = os.getenv("ORGANIZER_MODEL", "qwen2.5:7b")

# Temperaturas: Gerador criativo, Avaliadores e Organizador precisos
GENERATOR_TEMPERATURE = 0.7
EVALUATOR_TEMPERATURE = 0.1
STRONG_EVALUATOR_TEMPERATURE = 0.1
ORGANIZER_TEMPERATURE = 0.1

# Tentativas regulares por ciclo antes de acionar o avaliador forte
MAX_TENTATIVAS = 3
# Ciclos completos (regular + forte) antes de entregar com aviso
MAX_CICLOS = 2

# Auto-consistência numérica (agente verificador)
VERIFIER_SAMPLES = int(os.getenv("VERIFIER_SAMPLES", "3"))
VERIFIER_TEMPERATURE = float(os.getenv("VERIFIER_TEMPERATURE", "0.7"))

# Regra opcional de termos absolutos no validador de regras (desligada por padrão)
REGRA_TERMOS_ABSOLUTOS = os.getenv("REGRA_TERMOS_ABSOLUTOS", "false").lower() == "true"

BNCC_DATA_PATH = str(_PROJECT_ROOT / "data" / "bncc_matematica.json")
