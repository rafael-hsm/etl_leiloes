"""
Configurações centralizadas do projeto ETL Leilões
"""
import os
from pathlib import Path

# Diretório raiz do projeto
ROOT_DIR = Path(__file__).parent.parent

# Paths de dados
DATA_DIR = ROOT_DIR / "data"
JSON_FILE_PATH = DATA_DIR / "data.json"
SQLITE_DB_PATH = DATA_DIR / "etl_leiloes.db"

# Configurações do Scrapy
SCRAPY_PROJECT_NAME = "extract"
SCRAPY_SPIDER_NAME = "parque_leiloes"

# Configurações do Dashboard
DASH_HOST = "127.0.0.1"
DASH_PORT = 8050
DASH_DEBUG = True

# Configurações do Banco de Dados
DB_TABLE_NAME = "parque_leiloes_items"

# Configurações de Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Configurações do Spider
SPIDER_START_URL = "https://www.parquedosleiloes.com.br"
SPIDER_ALLOWED_DOMAINS = ["www.parquedosleiloes.com.br"]
SPIDER_CATEGORY = "VEÍCULOS"
SPIDER_STATUS = "Lances online agora"
