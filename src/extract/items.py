# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class EtlLeiloesVeicularItem(scrapy.Item):
    """Item schema para dados de lotes de veículos extraídos do Parque dos Leilões"""

    tipo_item = scrapy.Field()
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
    categoria = scrapy.Field()
    descricao = scrapy.Field()
    endereco = scrapy.Field()
    edital_url_detalhes = scrapy.Field()


class EditalItem(scrapy.Item):
    """Item schema para dados do edital (leilão) no Parque dos Leilões"""

    tipo_item = scrapy.Field()
    edital_nome = scrapy.Field()
    edital_data = scrapy.Field()
    edital_status = scrapy.Field()
    edital_categoria = scrapy.Field()
    edital_url_detalhes = scrapy.Field()
    edital_url_edital = scrapy.Field()
