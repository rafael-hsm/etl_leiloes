"""Testes de configuração"""
import sys
from pathlib import Path

# Adicionar o diretório config ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'config'))

def test_config_import():
    """Testa se as configurações podem ser importadas"""
    from settings import (
        ROOT_DIR,
        DATA_DIR,
        JSON_FILE_PATH,
        SQLITE_DB_PATH,
        DASH_HOST,
        DASH_PORT,
        DB_TABLE_NAME,
    )
    assert ROOT_DIR is not None
    assert DATA_DIR is not None
    assert JSON_FILE_PATH is not None
    assert SQLITE_DB_PATH is not None
    assert DASH_HOST == "127.0.0.1"
    assert DASH_PORT == 8050
    assert DB_TABLE_NAME == "parque_leiloes_items"

def test_paths_exist():
    """Testa se os paths são objetos Path válidos"""
    from settings import ROOT_DIR, DATA_DIR, JSON_FILE_PATH, SQLITE_DB_PATH
    assert isinstance(ROOT_DIR, Path)
    assert isinstance(DATA_DIR, Path)
    assert isinstance(JSON_FILE_PATH, Path)
    assert isinstance(SQLITE_DB_PATH, Path)

if __name__ == "__main__":
    test_config_import()
    test_paths_exist()
    print("Todos Os testes de configuração passaram!")
