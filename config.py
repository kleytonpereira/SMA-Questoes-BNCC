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
