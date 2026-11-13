import scrapy
import sys
from pathlib import Path

# Adicionar o diretório config ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / 'config'))
from settings import SPIDER_START_URL, SPIDER_ALLOWED_DOMAINS, SPIDER_CATEGORY, SPIDER_STATUS

from ..items import EtlLeiloesVeicularItem

class ParqueLeiloesSpider(scrapy.Spider):
    name = "parque_leiloes"
    allowed_domains = SPIDER_ALLOWED_DOMAINS
    start_urls = [SPIDER_START_URL]

    def __init__(self, *args, **kwargs):
        super(ParqueLeiloesSpider, self).__init__(*args, **kwargs)
        self.visited_pages = set()

    def parse(self, response):
        """Lista os leilões"""
        leiloes = response.xpath("//div[contains(@class, 'cards-list')]")
        
        for leilao in leiloes:
            status = leilao.xpath(".//span[contains(@class, 'badge')]/text()").getall()
            categoria = leilao.xpath(".//small[contains(@class, 'category')]/text()").getall()
            edital = leilao.xpath(".//a[contains(@class, 'btn-primary')]/@href").getall()
            detalhes = leilao.xpath(".//a[contains(@class, 'btn-secondary')]/@href").getall()

            # Certifique-se de que todas as listas tenham o mesmo tamanho
            for i in range(len(categoria)):
                # if categoria[i] == SPIDER_CATEGORY:  # Usar para percorer todos os leilões ativos ou não
                if categoria[i] == SPIDER_CATEGORY and status[i] == SPIDER_STATUS:  # Usar para percorer todos os leilões ativos
                    detalhes_url = detalhes[i]
                    self.logger.info(f"Seguindo para os detalhes do leilão: {detalhes_url}")
                    yield response.follow(detalhes_url, self.parse_detalhes_leilao)
                    
    def parse_detalhes_leilao(self, response):
        current_page = response.url.split('page=')[-1]
        if current_page in self.visited_pages:
            self.logger.info(f"Página {current_page} já visitada, ignorando.")
            return
        self.visited_pages.add(current_page)
        
        lotes = response.xpath('//div[contains(@class, "card-header")]')
        
        self.logger.info(f"Encontrados {len(lotes)} lotes na página {response.url}")

        for lote in lotes:
            link = lote.xpath(".//a/@href").get()
            link_url = response.urljoin(link)
            self.logger.info(f"Seguindo para os detalhes do lote: {link_url}")
            yield response.follow(link_url, self.parse_detalhes_lote)

        # Melhorar a lógica de paginação
        next_page = response.xpath("//ul[contains(@class, 'pagination')]//li[@class='page-item']/a[@rel='next']/@href").get()
        
        if next_page:
            next_page_url = response.urljoin(next_page)
            self.logger.info(f"Seguindo para a próxima página: {next_page_url}")
            yield response.follow(next_page_url, self.parse_detalhes_leilao)
    
    def parse_detalhes_lote(self, response):
        titulo_lote = response.xpath("//h3[contains(@class, 'title')]/span/text()").get()

        infos1 = response.xpath('//*[contains(concat(" ", @class, " "),concat(" ", "col-md-6", " "))][1]')
        infos2 = response.xpath('//*[contains(concat(" ", @class, " "),concat(" ", "col-md-6", " "))][2]')
        
        modelo = infos1.xpath(".//table//tr[1]/td[2]/text()").get(default='')
        marca = infos1.xpath(".//table//tr[2]/td[2]/text()").get(default='')
        ano = infos1.xpath(".//table//tr[3]/td[2]/text()").get(default='')
        valor_mercado = infos1.xpath(".//table//tr[4]/td[2]/text()").get(default='')
        
        cor = infos2.xpath(".//table//tr[1]/td[2]/text()").get(default='')
        combustivel = infos2.xpath(".//table//tr[2]/td[2]/text()").get(default='')
        quilometragem = infos2.xpath(".//table//tr[3]/td[2]/text()").get(default='')
        sinistro = infos2.xpath(".//table//tr[4]/td[2]/text()").get(default='')
        acessorios = response.xpath("//div[contains(@class, 'optionals')]//li/text()").getall()
        
        lances = response.xpath("//table[contains(@class, 'table last-bids-table ')]//tr")
        
        data_ultimo_lance = None
        valor_ultimo_lance = None
        total_lances = 0
        
        if lances:
            data_ultimo_lance = lances.xpath(".//td[2]/text()").get(default='')
            valor_ultimo_lance = lances.xpath(".//td[4]/text()").get(default='')
            total_lances = len(lances)
        
        item = EtlLeiloesVeicularItem()
        item['titulo_lote'] = titulo_lote
        item['url_lote'] = response.url
        item['modelo'] = modelo
        item['marca'] = marca
        item['ano'] = ano
        item['valor_mercado'] = valor_mercado
        item['cor'] = cor
        item['combustivel'] = combustivel
        item['quilometragem'] = quilometragem
        item['sinistro'] = sinistro
        item['acessorios'] = acessorios
        item['data_ultimo_lance'] = data_ultimo_lance
        item['valor_ultimo_lance'] = valor_ultimo_lance
        item['total_lances'] = total_lances

        yield item
