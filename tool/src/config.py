import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações gerais de API e modelo
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))

OPENAI_API_KEY_4 = os.getenv("OPENAI_API_KEY_4")
MODEL_NAME_4 = os.getenv("MODEL_NAME_4")

OPENAI_API_KEY_PROF = os.getenv("OPENAI_API_KEY_PROF")

# Configuração do servidor Joern
JOERN_SERVER_ENDPOINT = os.getenv("JOERN_SERVER_ENDPOINT", "http://localhost:9000")

# Configurações gerais do projeto
PROJECT_PATH = os.getenv("PROJECT_PATH", "./Dataset/wsvd-bench/src/main/java/pt/uc/dei/wsvdbench")
OUTPUT_JOERN_DIR = os.getenv("OUTPUT_JOERN_DIR", "./src/output_joern")

# Diretório de templates
TEMPLATE_CHATGPT_DIR = os.getenv("TEMPLATE_DIR", "./src/llm_integration/Chatgpt")
TEMPLATE_DEEP_DIR = os.getenv("TEMPLATE_DIR", "./src/llm_integration/templates/DeepSeek")

METHODS_JSON_PATH = os.getenv("METHODS_JSON_PATH", "./src/json_output/methods_structure.json")
OUTPUT_JSON_DIR = os.getenv("OUTPUT_JSON_DIR", "./src/json_output")

# Configurações de token e chat
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

LLM_CHOSEN = os.getenv("LLM_CHOSEN")
TEMPLATE_NUMBER = os.getenv("TEMPLATE_NUMBER")
TEMPLATE_VERSIONS = os.getenv("TEMPLATE_VERSIONS")

VM_PATH = os.getenv("VM_PATH")