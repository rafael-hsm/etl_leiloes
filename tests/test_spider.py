"""Testes do spider Scrapy usando fixtures de HTML reais"""
from pathlib import Path

import pytest
from scrapy.http import Request, TextResponse

from extract.items import EditalItem, EtlLeiloesVeicularItem
from extract.spiders.parque_leiloes import ParqueLeiloesSpider

FIXTURES_DIR = Path(__file__).parent / 'fixtures'


def make_response(fixture_name, url, meta=None):
    """Cria um TextResponse do Scrapy a partir de um fixture HTML"""
    body = (FIXTURES_DIR / fixture_name).read_text(encoding='utf-8')
    response = TextResponse(
        url=url,
        request=Request(url=url),
        body=body,
        encoding='utf-8',
    )
    if meta:
        response.meta.update(meta)
    return response


def split_output(output):
    """Separa items e requests gerados pelo spider"""
    output = list(output)
    items = [o for o in output if isinstance(o, (EditalItem, EtlLeiloesVeicularItem))]
    requests = [o for o in output if isinstance(o, Request)]
    return items, requests


@pytest.fixture
def spider():
    return ParqueLeiloesSpider()


class TestParseListagem:
    """Testes do parse() - seleção de editais de veículos"""

    def test_seleciona_apenas_veiculos(self, spider):
        response = make_response('home_veiculos.html', 'https://www.parquedosleiloes.com.br/')
        items, requests = split_output(spider.parse(response))

        # 3 editais de VEÍCULOS; IMÓVEIS e BENS E EQUIPAMENTOS são ignorados
        assert len(items) == 3
        assert len(requests) == 3
        urls = [r.url for r in requests]
        assert all('/leilao/9' in u for u in urls)
        assert not any('/leilao/99/' in u or '/leilao/97/' in u for u in urls)

    def test_ordem_ativos_primeiro(self, spider):
        response = make_response('home_veiculos.html', 'https://www.parquedosleiloes.com.br/')
        items, requests = split_output(spider.parse(response))

        # Ativos (online + em breve) primeiro, encerrados depois
        ids = [r.url.split('/leilao/')[1].split('/')[0] for r in requests]
        assert ids == ['90', '91', '92']
        statuses = [i['edital_status'] for i in items]
        assert statuses == ['Lances online agora', 'EM BREVE', 'Encerrado']

    def test_item_edital_tem_campos_completos(self, spider):
        response = make_response('home_veiculos.html', 'https://www.parquedosleiloes.com.br/')
        items, _ = split_output(spider.parse(response))

        edital = items[0]
        assert edital['tipo_item'] == 'edital'
        assert edital['edital_nome'] == 'LEILÃO VEÍCULOS ATIVO'
        assert edital['edital_data'] == '20 nov 2026, 10:00'
        assert edital['edital_status'] == 'Lances online agora'
        assert edital['edital_categoria'] == 'VEICULOS'
        assert edital['edital_url_detalhes'].endswith('/leilao/90/detalhes')
        assert edital['edital_url_edital'].endswith('/leilao/90/edital')

    def test_limite_de_5_editais(self, spider):
        """Com mais de 5 veículos, seleciona no máximo 5"""
        many_cards = '\n'.join(
            f'''<div class="card auction-card"><div class="card-body"><div class="text">
            <span class="badge badge-gray">Encerrado</span>
            <small class="date">0{i} out 2026, 10:00</small>
            <span class="name">VEICULO {i}</span>
            <small class="category">VEICULOS</small>
            </div><div class="details"><div class="buttons">
            <a href="https://www.parquedosleiloes.com.br/leilao/{80+i}/detalhes"
               class="btn btn-sm btn-secondary">Detalhes</a>
            </div></div></div></div>'''
            for i in range(8)
        )
        html = f'<html><body><div class="cards-list">{many_cards}</div></body></html>'
        response = TextResponse(
            url='https://www.parquedosleiloes.com.br/',
            request=Request(url='https://www.parquedosleiloes.com.br/'),
            body=html,
            encoding='utf-8',
        )
        items, requests = split_output(spider.parse(response))
        assert len(items) == 5
        assert len(requests) == 5

    def test_request_leva_callback_detalhes(self, spider):
        response = make_response('home_veiculos.html', 'https://www.parquedosleiloes.com.br/')
        _, requests = split_output(spider.parse(response))
        assert requests[0].callback == spider.parse_detalhes_leilao

    def test_fallback_sem_veiculo_usa_mais_recente(self, spider):
        """Sem nenhum veículo, usa o leilão mais recente do site"""
        response = make_response('home_sem_veiculo.html', 'https://www.parquedosleiloes.com.br/')
        items, requests = split_output(spider.parse(response))

        assert len(items) == 1
        assert len(requests) == 1
        assert '/leilao/96/detalhes' in requests[0].url


class TestParseDetalhesLeilao:
    """Testes do parse_detalhes_leilao() - página de detalhes do leilão"""

    def test_segue_apenas_lotes_nao_suspensos(self, spider):
        response = make_response(
            'detalhes_leilao.html',
            'https://www.parquedosleiloes.com.br/leilao/99/detalhes',
            meta={'categoria': 'IMÓVEIS', 'edital_url': 'https://www.parquedosleiloes.com.br/leilao/99/detalhes'},
        )
        requests = [r for r in spider.parse_detalhes_leilao(response) if isinstance(r, Request)]

        # Lote 1 está "Suspenso" e deve ser ignorado
        assert len(requests) == 1
        assert '/leilao/99/lote/2' in requests[0].url
        assert requests[0].meta['categoria'] == 'IMÓVEIS'
        assert requests[0].meta['edital_url'].endswith('/leilao/99/detalhes')

    def test_pagina_ja_visitada_e_ignorada(self, spider):
        url = 'https://www.parquedosleiloes.com.br/leilao/99/detalhes?page=2'
        response = make_response('detalhes_leilao.html', url, meta={'categoria': 'IMÓVEIS'})
        spider.visited_pages.add('2')
        requests = [r for r in spider.parse_detalhes_leilao(response) if isinstance(r, Request)]
        assert requests == []


class TestParseDetalhesLote:
    """Testes do parse_detalhes_lote() - página do lote"""

    META = {
        'categoria': 'VEICULOS',
        'edital_url': 'https://www.parquedosleiloes.com.br/leilao/98/detalhes',
    }

    def test_lote_imovel(self, spider):
        response = make_response(
            'lote_imovel.html',
            'https://www.parquedosleiloes.com.br/leilao/99/lote/2',
            meta={'categoria': 'IMÓVEIS', 'edital_url': 'https://www.parquedosleiloes.com.br/leilao/99/detalhes'},
        )
        items = list(spider.parse_detalhes_lote(response))

        assert len(items) == 1
        item = items[0]
        assert isinstance(item, EtlLeiloesVeicularItem)
        assert item['tipo_item'] == 'lote'
        assert item['titulo_lote'] == 'IMÓVEL TESTE/GO'
        assert item['categoria'] == 'IMÓVEIS'
        assert 'matrícula' in item['descricao']
        assert item['endereco'] == 'Cidade Teste, GO, Brasil'
        # Imóvel não tem campos de veículo
        assert item['modelo'] == ''
        assert item['marca'] == ''
        # Sem lances
        assert item['total_lances'] == 0
        assert item['data_ultimo_lance'] is None
        assert item['valor_ultimo_lance'] is None
        # Vínculo com o edital
        assert item['edital_url_detalhes'].endswith('/leilao/99/detalhes')

    def test_lote_veiculo(self, spider):
        response = make_response(
            'lote_veiculo.html',
            'https://www.parquedosleiloes.com.br/leilao/98/lote/13',
            meta=self.META,
        )
        items = list(spider.parse_detalhes_lote(response))

        assert len(items) == 1
        item = items[0]
        assert item['tipo_item'] == 'lote'
        assert item['modelo'] == 'GOL 1.0'
        assert item['marca'] == 'VW'
        assert item['ano'] == '2020'
        assert item['cor'] == 'BRANCA'
        assert item['combustivel'] == 'FLEX'
        assert item['quilometragem'] == '40000'
        assert item['sinistro'] == 'Não'
        assert item['valor_mercado'] == 'R$ 50.000,00 / janeiro de 2025'
        assert item['acessorios'] == ['AR CONDICIONADO', 'FREIOS ABS']
        assert item['categoria'] == 'VEICULOS'
        assert item['edital_url_detalhes'].endswith('/leilao/98/detalhes')
        # Últimos lances
        assert item['total_lances'] == 2
        assert item['data_ultimo_lance'] == '01/01/26 10:00:00.000'
        assert item['valor_ultimo_lance'] == 'R$ 40.000,00'
