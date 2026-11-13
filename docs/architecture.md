# Arquitetura do Projeto ETL Leilões

## Visão Geral

Projeto ETL (Extract, Transform, Load) para processar dados de leilões veiculares do Parque dos Leilões.

## Fluxo de Dados

```
Parque dos Leilões → Scrapy (Extract) → JSON → Pandas (Transform) → SQLite → Dash (Visualize)
```

## Componentes

### 1. Extract (src/extract/)
- Scrapy spider que coleta dados do site
- Filtra leilões de veículos ativos
- Extrai detalhes de lotes e lances
- Saída: data/data.json

### 2. Transform (src/transform/)
- Pandas processa o JSON
- Converte tipos, renomeia colunas
- Adiciona timestamp de coleta
- Saída: data/etl_leiloes.db

### 3. Visualize (src/visualize/)
- Dashboard Dash com análises
- Carros mais procurados, sem lances, melhores negócios
- Filtros por marca/modelo
- Acesso: http://127.0.0.1:8050/

## Configuração

Todas as configs estão em `config/settings.py`:
- Paths de arquivos
- Configurações de banco
- Configurações do servidor
- Configurações do spider
