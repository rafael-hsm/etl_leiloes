import scrapy

class ParqueLeiloesSpider(scrapy.Spider):
    name = "parque_leiloes"
    allowed_domains = ["www.parquedosleiloes.com.br"]
    start_urls = ["https://www.parquedosleiloes.com.br"]

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
                # if categoria[i] == 'VEÍCULOS':  # Usar para percorer todos os leilões ativos ou não
                if categoria[i] == 'VEÍCULOS' and status[i] == 'Lances online agora':  # Usar para percorer todos os leilões ativos
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
        
        item = {
            "titulo_lote": titulo_lote,
            "url_lote": response.url,
            "modelo": modelo,
            "marca": marca,
            "ano": ano,
            "valor_mercado": valor_mercado,
            "cor": cor,
            "combustivel": combustivel,
            "quilometragem": quilometragem,
            "sinistro": sinistro,
            "acessorios": acessorios,
            "data último lance": data_ultimo_lance,
            "valor último lance": valor_ultimo_lance,
            "total lances": total_lances
        }

        yield item
