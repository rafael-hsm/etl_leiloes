"""Testes da transformação JSON -> SQLite (tabelas editais + lotes)"""
import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).parent.parent
TRANSFORM_PATH = ROOT_DIR / 'src' / 'transform' / 'main.py'

EDITAL_URL = 'https://example.com/leilao/1/detalhes'


def load_transform_module():
    """Carrega o módulo de transformação (executa o ETL na importação)"""
    spec = importlib.util.spec_from_file_location('transform_main', TRANSFORM_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def transform_env(tmp_path, monkeypatch):
    """Executa a transformação com JSON e SQLite temporários"""
    import settings as cfg

    data = [
        # Item de edital
        {
            "tipo_item": "edital",
            "edital_nome": "LEILÃO TESTE",
            "edital_data": "20 nov 2026, 10:00",
            "edital_status": "Lances online agora",
            "edital_categoria": "VEICULOS",
            "edital_url_detalhes": EDITAL_URL,
            "edital_url_edital": "https://example.com/leilao/1/edital",
        },
        # Lote de imóvel (campos de veículo vazios)
        {
            "tipo_item": "lote",
            "titulo_lote": "IMÓVEL TESTE",
            "url_lote": "https://example.com/lote/1",
            "categoria": "IMÓVEIS",
            "edital_url_detalhes": EDITAL_URL,
            "descricao": "Descrição do imóvel",
            "endereco": "Cidade, UF, Brasil",
            "modelo": "",
            "marca": "",
            "ano": "",
            "acessorios": [],
            "data_ultimo_lance": None,
            "valor_ultimo_lance": None,
            "total_lances": 0,
        },
        # Lote de veículo
        {
            "tipo_item": "lote",
            "titulo_lote": "GOL 2020",
            "url_lote": "https://example.com/lote/2",
            "categoria": "VEICULOS",
            "edital_url_detalhes": EDITAL_URL,
            "modelo": "GOL",
            "marca": "VW",
            "ano": "2020",
            "acessorios": ["AR CONDICIONADO", "FREIOS ABS"],
            "data_ultimo_lance": "01/01/26 10:00:00",
            "valor_ultimo_lance": "R$ 40.000,00",
            "total_lances": 5,
        },
    ]

    json_path = tmp_path / 'data.json'
    db_path = tmp_path / 'test.db'
    json_path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')

    monkeypatch.setattr(cfg, 'JSON_FILE_PATH', json_path)
    monkeypatch.setattr(cfg, 'SQLITE_DB_PATH', db_path)
    monkeypatch.setattr(cfg, 'DB_TABLE_NAME', 'test_lotes')
    monkeypatch.setattr(cfg, 'EDITAIS_TABLE_NAME', 'test_editais')

    load_transform_module()
    return db_path


def read_table(db_path, table):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(f"SELECT * FROM {table}").fetchall()
    conn.close()
    return [dict(r) for r in rows]


class TestTransform:
    def test_gera_tabelas_editais_e_lotes(self, transform_env):
        editais = read_table(transform_env, 'test_editais')
        lotes = read_table(transform_env, 'test_lotes')
        assert len(editais) == 1
        assert len(lotes) == 2

    def test_edital_campos(self, transform_env):
        editais = read_table(transform_env, 'test_editais')
        ed = editais[0]
        assert ed['nome'] == 'LEILÃO TESTE'
        assert ed['status'] == 'Lances online agora'
        assert ed['categoria'] == 'VEICULOS'
        assert ed['url_detalhes'] == EDITAL_URL
        assert ed['url_edital'].endswith('/edital')
        assert 'id' in ed
        assert '_data_coleta' in ed

    def test_lotes_vinculados_ao_edital(self, transform_env):
        editais = read_table(transform_env, 'test_editais')
        lotes = read_table(transform_env, 'test_lotes')
        edital_id = editais[0]['id']
        assert all(l['edital_id'] == edital_id for l in lotes)

    def test_campos_de_imovel_e_veiculo(self, transform_env):
        lotes = read_table(transform_env, 'test_lotes')
        imovel = next(l for l in lotes if l['titulo_lote'] == 'IMÓVEL TESTE')
        veiculo = next(l for l in lotes if l['titulo_lote'] == 'GOL 2020')

        assert imovel['endereco'] == 'Cidade, UF, Brasil'
        assert imovel['modelo'] == ''
        assert veiculo['modelo'] == 'GOL'
        assert veiculo['marca'] == 'VW'

    def test_acessorios_convertidos_para_string(self, transform_env):
        lotes = read_table(transform_env, 'test_lotes')
        veiculo = next(l for l in lotes if l['titulo_lote'] == 'GOL 2020')
        assert veiculo['acessorios'] == 'AR CONDICIONADO, FREIOS ABS'

    def test_colunas_padronizadas_e_data_coleta(self, transform_env):
        lotes = read_table(transform_env, 'test_lotes')
        assert 'data último lance' in lotes[0]
        assert 'valor último lance' in lotes[0]
        assert 'total lances' in lotes[0]
        assert '_data_coleta' in lotes[0]

    def test_json_inexistente_nao_falha(self, tmp_path, monkeypatch):
        """Quando o JSON não existe, o script não deve quebrar"""
        import settings as cfg
        monkeypatch.setattr(cfg, 'JSON_FILE_PATH', tmp_path / 'nao_existe.json')
        monkeypatch.setattr(cfg, 'SQLITE_DB_PATH', tmp_path / 'vazio.db')
        load_transform_module()  # não deve levantar exceção
