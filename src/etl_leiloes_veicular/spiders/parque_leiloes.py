import scrapy

class ParqueLeiloesSpider(scrapy.Spider):
    name = "parque_leiloes"
    allowed_domains = ["www.parquedosleiloes.com.br"]
    start_urls = ["https://www.parquedosleiloes.com.br"]

    def parse(self, response):
        """Lista os leilões ativos."""
        leiloes = response.xpath("//div[contains(@class, 'cards-list')]")
        
        for leilao in leiloes:
            status = leilao.xpath(".//span[contains(@class, 'badge ')]/text()").getall()
            data = leilao.xpath(".//small[contains(@class, 'date')]/text()").getall()
            categoria = leilao.xpath(".//small[contains(@class, 'category')]/text()").getall()
            edital = leilao.xpath(".//a[contains(@class, 'btn-primary')]/@href").getall()
            detalhes = leilao.xpath(".//a[contains(@class, 'btn-secondary')]/@href").getall()

            # Certifique-se de que todas as listas tenham o mesmo tamanho
            
            for i in range(len(categoria)):
                if categoria[i] == 'VEÍCULOS':
                    if status[i] == 'Lances online agora':
                        detalhes_url = detalhes[i]
                        # yield {
                        #     "status": status[i],
                        #     "data": data[i],
                        #     "categoria": categoria[i],
                        #     "edital": edital[i],
                        #     "detalhes": detalhes[i],
                        # }
                        yield response.follow(detalhes_url, self.parse_detalhes_leilao)
                    
    def parse_detalhes_leilao(self, response):
        lotes = response.xpath('//div[contains(@class, "card-header")]')
        
        for lote in lotes:
            link = lote.xpath(".//a/@href").get()
            
            yield response.follow(link, self.parse_detalhes_lote)

        pagination = response.xpath("//ul[contains(@class, 'pagination')]")
        next_page_url = pagination.xpath(".//li[contains(@class, 'page-item')]/a/@href").get()
        
        if next_page_url:
            yield response.follow(url=next_page_url, callback=self.parse_detalhes_leilao)
    
    def parse_detalhes_lote(self, response):
        titulo_lote = response.xpath("//h3[contains(@class, 'title')]/span/text()").get()
        
        infos1 = response.xpath('//*[contains(concat(" ", @class, " "),concat(" ", "col-md-6", " "))][1]')
        
        for info in infos1:
            modelo = info.xpath(".//table//tr[1]/td[2]/text()").get()
            marca = info.xpath(".//table//tr[2]/td[2]/text()").get()
            ano = info.xpath(".//table//tr[3]/td[2]/text()").get()
            valor_mercado = info.xpath(".//table//tr[4]/td[2]/text()").get()
            
        infos2 = response.xpath('//*[contains(concat(" ", @class, " "),concat(" ", "col-md-6", " "))][2]')
        
        for info in infos2:  
            cor = info.xpath(".//table//tr[1]/td[2]/text()").get()
            combustivel = info.xpath(".//table//tr[2]/td[2]/text()").get()
            quilometragem = info.xpath(".//table//tr[3]/td[2]/text()").get()
            sinistro = info.xpath(".//table//tr[4]/td[2]/text()").get()
            acessorios = response.xpath("//div[contains(@class, 'optionals')]//li/text()/text()").getall()
        
        lances = response.xpath("//table[contains(@class, 'table last-bids-table ')]")
        
        for lance in lances:
            data_ultimo_lance = lance.xpath(".//tr[1]/td[2]/text()").get()
            valor_ultimo_lance = lance.xpath(".//tr[1]/td[4]/text()").get()
            total_lances = len(lance.xpath(".//tr").getall())
        
        yield {
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
