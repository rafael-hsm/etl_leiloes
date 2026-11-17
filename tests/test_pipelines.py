"""Testes dos pipelines e middlewares do Scrapy"""
import pytest

from extract.items import EtlLeiloesVeicularItem
from extract.pipelines import EtlLeiloesVeicularPipeline
from extract.middlewares import (
    EtlLeiloesVeicularSpiderMiddleware,
    EtlLeiloesVeicularDownloaderMiddleware,
)
from extract.spiders.parque_leiloes import ParqueLeiloesSpider


class TestItems:
    def test_item_aceita_campos_esperados(self):
        item = EtlLeiloesVeicularItem()
        item['titulo_lote'] = 'Teste'
        item['categoria'] = 'IMÓVEIS'
        item['descricao'] = 'Desc'
        item['endereco'] = 'Cidade, UF'
        assert item['titulo_lote'] == 'Teste'
        assert item['categoria'] == 'IMÓVEIS'


class TestPipeline:
    def test_process_item_retorna_item(self):
        pipeline = EtlLeiloesVeicularPipeline()
        item = EtlLeiloesVeicularItem(titulo_lote='Teste')
        result = pipeline.process_item(item, spider=None)
        assert result is item


class TestSpiderMiddleware:
    def test_spider_opened_loga(self, caplog):
        middleware = EtlLeiloesVeicularSpiderMiddleware()
        spider = ParqueLeiloesSpider()
        with caplog.at_level('INFO'):
            middleware.spider_opened(spider)
        assert 'parque_leiloes' in caplog.text

    def test_process_spider_output_retorna_resultado(self):
        middleware = EtlLeiloesVeicularSpiderMiddleware()
        items = [EtlLeiloesVeicularItem(), EtlLeiloesVeicularItem()]
        assert list(middleware.process_spider_output(None, items, None)) == items


class TestDownloaderMiddleware:
    def test_process_request_retorna_none(self):
        middleware = EtlLeiloesVeicularDownloaderMiddleware()
        assert middleware.process_request(None, None) is None

    def test_process_response_retorna_response(self):
        middleware = EtlLeiloesVeicularDownloaderMiddleware()
        response = object()
        assert middleware.process_response(None, response, None) is response
