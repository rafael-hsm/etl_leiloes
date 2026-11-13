# ETL - Leilão Veicular

## Extração, Transformação e Apresentação de dados Extraídos do site: [Parque dos Leilões](https://www.parquedosleiloes.com.br/)

Projeto para extração de dados de leilão de veículos. **NOS VALORES FINAIS NÃO FORAM CALCULADAS AS TAXAS DO LEILÃO.**

## Estrutura do Projeto

```
etl_leiloes/
├── config/           # Configurações centralizadas
├── data/             # Dados extraídos e banco SQLite
├── docs/             # Documentação técnica
├── scripts/          # Scripts utilitários
├── src/
│   ├── extract/      # Spiders Scrapy (extração)
│   ├── transform/    # Scripts de transformação JSON → SQLite
│   └── visualize/   # Dashboard Dash (visualização)
├── tests/            # Suite de testes
└── requirements.txt  # Dependências Python
```

## Instalação

```bash
# Executar script de setup
bash setup.sh

# Ou manualmente:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

### 1. Extração (Web Scraping)

```bash
cd src
scrapy crawl parque_leiloes -O ../data/data.json
```

### 2. Transformação (JSON → SQLite)

```bash
python3 src/transform/main.py
```

### 3. Visualização (Dashboard)

```bash
python3 src/visualize/app.py
```

Abra o navegador e acesse http://127.0.0.1:8050/ para visualizar o dashboard.

## Funcionalidades do Dashboard

- **Carros Mais Procurados**: Veículos com mais de 9 lances
- **Carros Sem Lances**: Veículos que não receberam lances
- **Melhores Negócios**: Oportunidades calculadas (valor de mercado - último lance)
- **Filtros**: Filtrar por marca e modelo
- **Tabela Completa**: Todos os dados com paginação e ordenação
