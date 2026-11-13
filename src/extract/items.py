# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class EtlLeiloesVeicularItem(scrapy.Item):
    """Item schema para dados de leilões veiculares extraídos do Parque dos Leilões"""
    
    titulo_lote = scrapy.Field()
    url_lote = scrapy.Field()
    modelo = scrapy.Field()
    marca = scrapy.Field()
    ano = scrapy.Field()
    valor_mercado = scrapy.Field()
    cor = scrapy.Field()
    combustivel = scrapy.Field()
    quilometragem = scrapy.Field()
    sinistro = scrapy.Field()
    acessorios = scrapy.Field()
    data_ultimo_lance = scrapy.Field()
    valor_ultimo_lance = scrapy.Field()
    total_lances = scrapy.Field()
