import scrapy
import sys
import re
import unicodedata
from pathlib import Path

# Adicionar o diretório config ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'config'))
from settings import (
    SPIDER_START_URL, SPIDER_ALLOWED_DOMAINS, SPIDER_CATEGORIES,
    SPIDER_STATUS, SPIDER_STATUS_EM_BREVE, SPIDER_MAX_EDITAIS,
)

from ..items import EtlLeiloesVeicularItem, EditalItem


def _norm(text):
    """Normaliza texto para comparação: remove acentos, espaços extras e uppercase."""
    text = ' '.join((text or '').split())
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    ).strip().upper()


class ParqueLeiloesSpider(scrapy.Spider):
    name = "parque_leiloes"
    allowed_domains = SPIDER_ALLOWED_DOMAINS
    start_urls = [SPIDER_START_URL]

    # Status considerados "em andamento": recebendo lances ou abrindo em breve
    STATUS_ATIVOS = {_norm(SPIDER_STATUS), _norm(SPIDER_STATUS_EM_BREVE)}

    def __init__(self, *args, **kwargs):
        super(ParqueLeiloesSpider, self).__init__(*args, **kwargs)
        self.visited_pages = set()
        self.categories = {_norm(c) for c in SPIDER_CATEGORIES}
        self.max_editais = SPIDER_MAX_EDITAIS

    def parse(self, response):
        """Lista os leilões e seleciona até SPIDER_MAX_EDITAIS editais de veículos.

        Ordem de prioridade: editais com lances em aberto ("Lances online
        agora") ou para abrir em breve ("EM BREVE") primeiro, depois os
        demais (ex.: "Encerrado"). A listagem já vem ordenada por data.
        """
        cards = response.xpath("//div[contains(@class, 'auction-card')]")

        candidatos = []
        for card in cards:
            badge = card.xpath(".//span[contains(@class, 'badge')]/text()").get()
            status = _norm(badge)
            categoria = ' '.join(
                card.xpath(".//small[contains(@class, 'category')]/text()").getall()
            ).strip()
            detalhes = card.xpath(".//a[contains(@class, 'btn-secondary')]/@href").get()
            edital = card.xpath(".//a[contains(@class, 'btn-primary')]/@href").get()
            nome = ' '.join(
                card.xpath(".//span[contains(@class, 'name')]/text()").getall()
            ).strip()
            data = ' '.join(
                card.xpath(".//small[contains(@class, 'date')]/text()").getall()
            ).strip()

            if not detalhes:
                continue

            candidatos.append({
                'categoria': categoria,
                'categoria_match': _norm(categoria) in self.categories,
                'status': status,
                'status_badge': badge,
                'nome': nome,
                'data': data,
                'url_detalhes': response.urljoin(detalhes),
                'url_edital': response.urljoin(edital) if edital else '',
            })

        # Apenas editais das categorias configuradas (hoje: VEÍCULOS)
        veiculos = [c for c in candidatos if c['categoria_match']]

        if veiculos:
            ativos = [c for c in veiculos if c['status'] in self.STATUS_ATIVOS]
            demais = [c for c in veiculos if c['status'] not in self.STATUS_ATIVOS]
            selecionados = (ativos + demais)[:self.max_editais]
        else:
            # Fallback: nenhum veículo encontrado, usa o leilão mais recente
            selecionados = candidatos[:1]
            self.logger.info(
                "Nenhum edital de veículo encontrado. Usando o leilão mais recente."
            )

        for candidato in selecionados:
            # Item do próprio edital (alimenta a tabela `editais`)
            yield EditalItem(
                tipo_item='edital',
                edital_nome=candidato['nome'],
                edital_data=candidato['data'],
                edital_status=candidato['status_badge'],
                edital_categoria=candidato['categoria'],
                edital_url_detalhes=candidato['url_detalhes'],
                edital_url_edital=candidato['url_edital'],
            )

            self.logger.info(
                f"Seguindo para os detalhes do leilão: {candidato['url_detalhes']}"
            )
            yield response.follow(
                candidato['url_detalhes'],
                self.parse_detalhes_leilao,
                meta={
                    'categoria': candidato['categoria'],
                    'edital_url': candidato['url_detalhes'],
                },
            )

    def parse_detalhes_leilao(self, response):
        current_page = response.url.split('page=')[-1]
        if current_page in self.visited_pages:
            self.logger.info(f"Página {current_page} já visitada, ignorando.")
            return
        self.visited_pages.add(current_page)

        meta_lote = {
            'categoria': response.meta.get('categoria', ''),
            'edital_url': response.meta.get('edital_url', ''),
        }
        categoria = meta_lote['categoria']
        lotes = response.xpath("//div[contains(@class, 'auction-lot-card')]")

        self.logger.info(f"Encontrados {len(lotes)} lotes na página {response.url}")

        for lote in lotes:
            # Ignora lotes suspensos
            status_lote = _norm(lote.xpath(".//span[contains(@class, 'lot-status-color')]/text()").get())
            if 'SUSPENSO' in status_lote:
                self.logger.info(f"Lote suspenso, ignorando: {lote.xpath('.//span[contains(@class, \'name\')]/text()').get()}")
                continue

            link = lote.xpath(".//div[contains(@class, 'buttons')]//a/@href").get()
            if not link:
                link = lote.xpath(".//a[contains(@href, '/lote/')]/@href").get()
            if not link:
                continue

            link_url = response.urljoin(link)
            self.logger.info(f"Seguindo para os detalhes do lote: {link_url}")
            yield response.follow(
                link_url,
                self.parse_detalhes_lote,
                meta=meta_lote,
            )

        # Paginação da página de detalhes do leilão
        next_page = response.xpath(
            "//ul[contains(@class, 'pagination')]//a[@rel='next' or contains(@class, 'next')]/@href"
        ).get()

        if next_page:
            next_page_url = response.urljoin(next_page)
            self.logger.info(f"Seguindo para a próxima página: {next_page_url}")
            yield response.follow(
                next_page_url,
                self.parse_detalhes_leilao,
                meta=meta_lote,
            )

    def parse_detalhes_lote(self, response):
        # Extrai pares rótulo/valor das tabelas de informações do lote
        # (veículos: Modelo, Marca, Ano, etc.; imóveis: Título, Descrição)
        info = {}
        # Veículos usam .auction-lot-vehicle; imóveis usam .auction-lot-property
        property_divs = response.xpath(
            "//div[contains(@class, 'auction-lot-property') or contains(@class, 'auction-lot-vehicle')]"
        )
        for table in property_divs.xpath(".//table[contains(@class, 'table-striped')]"):
            for tr in table.xpath(".//tr"):
                cells = [
                    ' '.join(c.xpath('.//text()').getall()).strip()
                    for c in tr.xpath("./td|./th")
                ]
                cells = [c for c in cells if c]
                if len(cells) >= 2:
                    key = cells[0].rstrip(':').strip().lower()
                    info[key] = ' '.join(cells[1:]).strip()

        # Endereço fica em .optionals (ex.: imóveis)
        endereco = ''
        opcionais = ' '.join(response.xpath("//div[contains(@class, 'optionals')]//text()").getall())
        if ':' in opcionais:
            endereco = opcionais.split(':', 1)[1].strip()

        acessorios = response.xpath("//div[contains(@class, 'optionals')]//li/text()").getall()

        # Últimos lances: colunas = data, usuário, tipo, valor
        lances = response.xpath("//table[contains(@class, 'last-bids-table')]//tr")

        data_ultimo_lance = None
        valor_ultimo_lance = None
        total_lances = 0

        bid_rows = [tr for tr in lances if len(tr.xpath('./td').getall()) >= 3]
        if bid_rows:
            primeiro = bid_rows[0]
            tds = [
                ' '.join(td.xpath('.//text()').getall()).strip()
                for td in primeiro.xpath('./td')
            ]
            # Localiza a data e o valor independentemente de colunas vazias
            data_ultimo_lance = next(
                (c for c in tds if re.search(r'\d{2}/\d{2}/\d{2}', c)), ''
            )
            valor_ultimo_lance = next(
                (c for c in reversed(tds) if 'R$' in c), ''
            )
            total_lances = len(bid_rows)

        item = EtlLeiloesVeicularItem()
        item['tipo_item'] = 'lote'
        item['titulo_lote'] = info.get('título') or response.xpath('//h1/text()').get('').strip()
        item['url_lote'] = response.url
        item['categoria'] = response.meta.get('categoria', '')
        item['edital_url_detalhes'] = response.meta.get('edital_url', '')
        item['descricao'] = info.get('descrição', '')
        item['endereco'] = endereco
        item['modelo'] = info.get('modelo', '')
        item['marca'] = info.get('marca', '')
        item['ano'] = info.get('ano', '')
        item['valor_mercado'] = info.get('valor de mercado', '')
        item['cor'] = info.get('cor', '')
        item['combustivel'] = info.get('combustível', '')
        item['quilometragem'] = info.get('quilometragem', '')
        item['sinistro'] = info.get('sinistro', '')
        item['acessorios'] = acessorios
        item['data_ultimo_lance'] = data_ultimo_lance
        item['valor_ultimo_lance'] = valor_ultimo_lance
        item['total_lances'] = total_lances

        yield item
