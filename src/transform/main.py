import json
import pandas as pd
import sqlite3
from datetime import datetime
import sys
import logging
from pathlib import Path

# Adicionar o diretório config ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'config'))
from settings import (
    JSON_FILE_PATH, SQLITE_DB_PATH, DB_TABLE_NAME, EDITAIS_TABLE_NAME,
    LOG_LEVEL, LOG_FORMAT,
)

# Configurar logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

EDITAL_COLUMNS = [
    'edital_nome', 'edital_data', 'edital_status',
    'edital_categoria', 'edital_url_detalhes', 'edital_url_edital',
]

if JSON_FILE_PATH.exists() and JSON_FILE_PATH.stat().st_size > 0:
    try:
        logger.info(f"Lendo arquivo JSON: {JSON_FILE_PATH}")
        # Ler o arquivo JSON manualmente - O scrapy gera uma lista de dicionários
        with open(JSON_FILE_PATH, 'r') as file:
            data = json.load(file)

        df_all = pd.DataFrame(data)
        logger.info(f"Carregados {len(df_all)} registros no DataFrame")

        # Separar itens de edital e itens de lote
        df_editais = df_all[df_all['tipo_item'] == 'edital'].copy()
        df_lotes = df_all[df_all['tipo_item'] == 'lote'].copy()
        logger.info(f"Editais: {len(df_editais)} | Lotes: {len(df_lotes)}")

        # Preencher valores ausentes (ex.: imóveis não têm campos de veículo)
        df_lotes = df_lotes.fillna('')

        # Converter a coluna 'acessorios' de listas para strings
        if 'acessorios' in df_lotes.columns:
            df_lotes['acessorios'] = df_lotes['acessorios'].apply(
                lambda x: ', '.join(x) if isinstance(x, list) else x
            )

        # Renomear colunas dos lotes para padronizar
        df_lotes = df_lotes.rename(columns={
            'data_ultimo_lance': 'data último lance',
            'valor_ultimo_lance': 'valor último lance',
            'total_lances': 'total lances'
        })

        # Conectar ao banco de dados SQLite (ou criar um novo)
        logger.info(f"Conectando ao banco SQLite: {SQLITE_DB_PATH}")
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        # Remover tabela legada se existir
        cursor.execute("DROP TABLE IF EXISTS parque_leiloes_items")

        # ===== Tabela de editais =====
        if not df_editais.empty:
            df_editais = df_editais[EDITAL_COLUMNS].drop_duplicates(
                subset=['edital_url_detalhes']
            )
            df_editais = df_editais.rename(columns={
                'edital_nome': 'nome',
                'edital_data': 'data',
                'edital_status': 'status',
                'edital_categoria': 'categoria',
                'edital_url_detalhes': 'url_detalhes',
                'edital_url_edital': 'url_edital',
            })
            df_editais['_data_coleta'] = datetime.now()
            df_editais.to_sql(EDITAIS_TABLE_NAME, conn, if_exists='replace', index=True, index_label='id')
            logger.info(f"{len(df_editais)} editais salvos na tabela '{EDITAIS_TABLE_NAME}'")

            # Mapa url_detalhes -> id do edital
            mapa_editais = dict(zip(df_editais['url_detalhes'], df_editais.index))
        else:
            mapa_editais = {}
            logger.warning("Nenhum item de edital encontrado no JSON")

        # ===== Tabela de lotes =====
        if not df_lotes.empty:
            # Adicionar a coluna _data_coleta com a data e hora atuais
            df_lotes['_data_coleta'] = datetime.now()

            # Vincular cada lote ao seu edital via FK
            df_lotes['edital_id'] = df_lotes['edital_url_detalhes'].map(mapa_editais)
            lotes_sem_edital = df_lotes['edital_id'].isna().sum()
            if lotes_sem_edital:
                logger.warning(f"{lotes_sem_edital} lotes sem edital correspondente")

            df_lotes.to_sql(DB_TABLE_NAME, conn, if_exists='replace', index=False)
            logger.info(f"{len(df_lotes)} lotes salvos na tabela '{DB_TABLE_NAME}'")
        else:
            logger.warning("Nenhum item de lote encontrado no JSON")

        # Fechar a conexão com o banco de dados
        conn.close()

        logger.info("Transformação concluída com sucesso")
        if not df_lotes.empty:
            logger.info(f"Primeiros registros:\n{df_lotes.head()}")
    except (ValueError, KeyError) as e:
        logger.error(f"Erro ao processar o arquivo JSON: {e}")
