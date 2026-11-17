FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependências primeiro para aproveitar o cache de camadas
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código do projeto
COPY . .

# Garantir que o diretório de dados existe
RUN mkdir -p data

# Por padrão, executa o pipeline ETL completo (extract + transform)
# Uso: docker run etl-leiloes transform   -> apenas transformação
#     docker run etl-leiloes visualize    -> dashboard (requer porta exposta)
CMD ["python3", "scripts/run_etl.py", "all"]
