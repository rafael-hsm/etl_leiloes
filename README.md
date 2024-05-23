# ETL - Leilão veícular
## Extração, Transofrmação e Apresentação de dados Extraídos do site: [Parque dos Leilões](https://www.parquedosleiloes.com.br/)
Projeto para extração de dados de leilão de veículos

## Para rodar o web scraping

```bash
scrapy crawl parque_leiloes -O ../../data/data.jsonl
```

Para rodar o PANDAS tem que fazer isso dentro da pasta SRC

```bash
python transformacao/main.py
```

Para rodar o Streamlit tem que fazer isso dentro da pasta SRC

```bash
streamlit run dashboard/app.py 
```
