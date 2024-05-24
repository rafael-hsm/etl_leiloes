import json
import os
import pandas as pd
import sqlite3
from datetime import datetime

# Obter o caminho absoluto do diretório onde o script está localizado
current_dir = os.path.dirname(os.path.abspath(__file__))

# Obter o caminho absoluto do diretório root do projeto
root_dir = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))

# Definir o caminho do arquivo JSON e do banco de dados SQLite dinamicamente
json_file_path = os.path.join(root_dir, 'data', 'data-disponivel.json')
sqlite_db_path = os.path.join(root_dir, 'data', 'etl_leiloes.db')

if os.path.exists(json_file_path) and os.path.getsize(json_file_path) > 0:
    try:
        # Ler o arquivo JSON manualmente - O scrapy gera uma lista de dicionários
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        # Carregar os dados no DataFrame
        df = pd.DataFrame(data)

        # Converter a coluna 'acessorios' de listas para strings
        if 'acessorios' in df.columns:
            df['acessorios'] = df['acessorios'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)

        # Adicionar a coluna _data_coleta com a data e hora atuais
        df['_data_coleta'] = datetime.now()

        # Conectar ao banco de dados SQLite (ou criar um novo)
        conn = sqlite3.connect(sqlite_db_path)

        # Salvar o DataFrame no banco de dados SQLite
        df.to_sql('parque_leiloes_items', conn, if_exists='replace', index=False)

        # Fechar a conexão com o banco de dados
        conn.close()

        print(df.head())
    except ValueError as e:
        print(f"Erro ao ler o arquivo JSON: {e}")
else:
    print("O arquivo JSON não existe ou está vazio.")
