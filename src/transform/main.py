import json
import pandas as pd
import sqlite3
from datetime import datetime
import sys
import logging
from pathlib import Path

# Adicionar o diretório config ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'config'))
from settings import JSON_FILE_PATH, SQLITE_DB_PATH, DB_TABLE_NAME, LOG_LEVEL, LOG_FORMAT

# Configurar logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

if JSON_FILE_PATH.exists() and JSON_FILE_PATH.stat().st_size > 0:
    try:
        logger.info(f"Lendo arquivo JSON: {JSON_FILE_PATH}")
        # Ler o arquivo JSON manualmente - O scrapy gera uma lista de dicionários
        with open(JSON_FILE_PATH, 'r') as file:
            data = json.load(file)

        # Carregar os dados no DataFrame
        df = pd.DataFrame(data)
        logger.info(f"Carregados {len(df)} registros no DataFrame")

        # Converter a coluna 'acessorios' de listas para strings
        if 'acessorios' in df.columns:
            df['acessorios'] = df['acessorios'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
        
        # Renomear colunas para padronizar (remover espaços e acentos)
        df = df.rename(columns={
            'data_ultimo_lance': 'data último lance',
            'valor_ultimo_lance': 'valor último lance',
            'total_lances': 'total lances'
        })

        # Adicionar a coluna _data_coleta com a data e hora atuais
        df['_data_coleta'] = datetime.now()

        # Conectar ao banco de dados SQLite (ou criar um novo)
        logger.info(f"Conectando ao banco SQLite: {SQLITE_DB_PATH}")
        conn = sqlite3.connect(SQLITE_DB_PATH)

        # Salvar o DataFrame no banco de dados SQLite
        df.to_sql(DB_TABLE_NAME, conn, if_exists='replace', index=False)
        logger.info(f"Dados salvos na tabela '{DB_TABLE_NAME}'")

        # Fechar a conexão com o banco de dados
        conn.close()

        logger.info("Transformação concluída com sucesso")
        logger.info(f"Primeiros registros:\n{df.head()}")
    except ValueError as e:
        logger.error(f"Erro ao ler o arquivo JSON: {e}")
except Exception as e:
    logger.error(f"Erro inesperado: {e}")
else:
    logger.warning("O arquivo JSON não existe ou está vazio.")
