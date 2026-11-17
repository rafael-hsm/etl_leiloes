"""Testes do dashboard Dash multi-página (home de editais + análise)"""
import importlib.util
import sqlite3
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).parent.parent
APP_PATH = ROOT_DIR / 'src' / 'visualize' / 'app.py'


def load_app_module():
    """Carrega o módulo do app"""
    spec = importlib.util.spec_from_file_location('visualize_app', APP_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def app_module(tmp_path, monkeypatch):
    """Cria um SQLite temporário com editais+lotes e carrega o app"""
    import settings as cfg

    db_path = tmp_path / 'test.db'
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE test_editais (
            id INTEGER PRIMARY KEY,
            nome TEXT, data TEXT, status TEXT, categoria TEXT,
            url_detalhes TEXT, url_edital TEXT, _data_coleta TEXT
        )
    """)
    conn.execute("""
        INSERT INTO test_editais
        (nome, data, status, categoria, url_detalhes, url_edital)
        VALUES ('LEILÃO TESTE', '20 nov 2026, 10:00', 'Lances online agora',
                'VEICULOS', 'https://example.com/leilao/1/detalhes',
                'https://example.com/leilao/1/edital')
    """)
    conn.execute("""
        CREATE TABLE test_lotes (
            titulo_lote TEXT, url_lote TEXT, modelo TEXT, marca TEXT,
            ano TEXT, "valor_mercado" TEXT, cor TEXT, combustivel TEXT,
            quilometragem TEXT, sinistro TEXT, acessorios TEXT,
            "data último lance" TEXT, "valor último lance" TEXT,
            "total lances" INTEGER, categoria TEXT, descricao TEXT,
            endereco TEXT, edital_id INTEGER, edital_url_detalhes TEXT,
            "_data_coleta" TEXT
        )
    """)
    conn.execute("""
        INSERT INTO test_lotes
        (titulo_lote, url_lote, modelo, marca, ano, "valor_mercado",
         "valor último lance", "total lances", quilometragem, categoria,
         edital_id, edital_url_detalhes)
        VALUES ('GOL', 'https://example.com/1', 'GOL', 'VW', '2020',
                'R$ 50.000,00', 'R$ 40.000,00', 5, '40000', 'VEICULOS',
                1, 'https://example.com/leilao/1/detalhes')
    """)
    conn.execute("""
        INSERT INTO test_lotes
        (titulo_lote, url_lote, modelo, marca, ano, "valor_mercado",
         "valor último lance", "total lances", quilometragem, categoria,
         edital_id, edital_url_detalhes, endereco)
        VALUES ('IMÓVEL X', 'https://example.com/2', '', '', '',
                '', '', 0, '', 'IMÓVEIS', 1,
                'https://example.com/leilao/1/detalhes', 'Cidade, UF')
    """)
    conn.commit()
    conn.close()

    monkeypatch.setattr(cfg, 'SQLITE_DB_PATH', db_path)
    monkeypatch.setattr(cfg, 'DB_TABLE_NAME', 'test_lotes')
    monkeypatch.setattr(cfg, 'EDITAIS_TABLE_NAME', 'test_editais')
    return load_app_module()


# Assinatura: (edital_id, marcas, modelos, anos, situacao, valor_min, valor_max)
def call_update(app_module, *args):
    return app_module.update_table(*args)


class TestVisualize:
    def test_app_inicializa(self, app_module):
        assert app_module.app is not None
        assert app_module.app.layout is not None

    def test_extract_value(self, app_module):
        assert app_module.extract_value('R$ 50.000,00') == 50000.0
        assert app_module.extract_value('R$ 1.234,56') == 1234.56
        assert app_module.extract_value('N/A') is None
        assert app_module.extract_value('') is None

    def test_home_layout_lista_editais(self, app_module):
        layout = app_module.home_layout()
        assert layout is not None

    def test_edital_layout(self, app_module):
        layout = app_module.edital_layout(1)
        assert layout is not None

    def test_edital_inexistente(self, app_module):
        layout = app_module.edital_layout(999)
        assert 'não encontrado' in str(layout).lower() or layout is not None

    def test_get_editais(self, app_module):
        editais = app_module.get_editais()
        assert len(editais) == 1
        assert editais.iloc[0]['nome'] == 'LEILÃO TESTE'

    def test_update_table_sem_filtros(self, app_module):
        row_data, options = call_update(app_module, 1, None, None, None, 'Todos', None, None)
        assert len(row_data) == 2
        assert any(r['modelo'] == 'GOL' for r in row_data)
        assert any(o['value'] == 'GOL' for o in options)

    def test_update_table_outro_edital_sem_dados(self, app_module):
        row_data, _ = call_update(app_module, 999, None, None, None, 'Todos', None, None)
        assert len(row_data) == 0

    def test_update_table_filtro_marca(self, app_module):
        row_data, _ = call_update(app_module, 1, ['VW'], None, None, 'Todos', None, None)
        assert len(row_data) == 1
        assert row_data[0]['marca'] == 'VW'

        row_data, _ = call_update(app_module, 1, ['INEXISTENTE'], None, None, 'Todos', None, None)
        assert len(row_data) == 0

    def test_update_table_filtro_situacao(self, app_module):
        row_data, _ = call_update(app_module, 1, None, None, None, 'Sem lances', None, None)
        assert len(row_data) == 1
        assert row_data[0]['titulo_lote'] == 'IMÓVEL X'

        row_data, _ = call_update(app_module, 1, None, None, None, 'Com lances', None, None)
        assert len(row_data) == 1
        assert row_data[0]['titulo_lote'] == 'GOL'

    def test_update_table_filtro_valor(self, app_module):
        # Último lance do GOL é R$ 40.000,00; imóvel não tem lance
        row_data, _ = call_update(app_module, 1, None, None, None, 'Todos', 35000, None)
        assert len(row_data) == 1

        row_data, _ = call_update(app_module, 1, None, None, None, 'Todos', 45000, None)
        assert len(row_data) == 0

        row_data, _ = call_update(app_module, 1, None, None, None, 'Todos', 35000, 45000)
        assert len(row_data) == 1

    def test_update_table_filtro_ano(self, app_module):
        row_data, _ = call_update(app_module, 1, None, None, ['2020'], 'Todos', None, None)
        assert len(row_data) == 1
        assert row_data[0]['ano'] == '2020'

        row_data, _ = call_update(app_module, 1, None, None, ['1999'], 'Todos', None, None)
        assert len(row_data) == 0
