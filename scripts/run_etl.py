#!/usr/bin/env python3
"""
Script de execução unificado para o pipeline ETL
Uso: python scripts/run_etl.py [extract|transform|visualize|all]
"""
import sys
import subprocess
import argparse
import logging
from pathlib import Path

# Adicionar o diretório config ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'config'))
from settings import LOG_LEVEL, LOG_FORMAT

# Configurar logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

def run_extract():
    """Executa a extração com Scrapy"""
    logger.info("=== Iniciando Extração (Scrapy) ===")
    src_dir = Path(__file__).parent.parent / "src"
    result = subprocess.run(
        [sys.executable, "-m", "scrapy", "crawl", "parque_leiloes",
         "-O", "../data/data.json"],
        cwd=src_dir,
        capture_output=True,
        text=True
    )
    logger.info(result.stdout)
    if result.stderr:
        logger.error(result.stderr)
    if result.returncode == 0:
        logger.info("✓ Extração concluída com sucesso")
    else:
        logger.error("✗ Extração falhou")
        sys.exit(1)

def run_transform():
    """Executa a transformação JSON → SQLite"""
    logger.info("=== Iniciando Transformação ===")
    result = subprocess.run(
        [sys.executable, "src/transform/main.py"],
        capture_output=True,
        text=True
    )
    logger.info(result.stdout)
    if result.stderr:
        logger.error(result.stderr)
    if result.returncode == 0:
        logger.info("✓ Transformação concluída com sucesso")
    else:
        logger.error("✗ Transformação falhou")
        sys.exit(1)

def run_visualize():
    """Executa o dashboard Dash"""
    logger.info("=== Iniciando Dashboard ===")
    logger.info("Acesse http://127.0.0.1:8050/ no navegador")
    result = subprocess.run(
        [sys.executable, "src/visualize/app.py"],
        text=True
    )
    if result.returncode != 0:
        logger.error("✗ Dashboard falhou")
        sys.exit(1)

def run_all():
    """Executa o pipeline completo ETL"""
    logger.info("=== Executando Pipeline ETL Completo ===")
    run_extract()
    run_transform()
    logger.info("\n=== Pipeline ETL concluído ===")
    logger.info("Para visualizar os dados, execute: python scripts/run_etl.py visualize")

def main():
    parser = argparse.ArgumentParser(description="Executa o pipeline ETL de leilões")
    parser.add_argument(
        "stage",
        choices=["extract", "transform", "visualize", "all"],
        help="Estágio do pipeline a executar"
    )
    args = parser.parse_args()

    if args.stage == "extract":
        run_extract()
    elif args.stage == "transform":
        run_transform()
    elif args.stage == "visualize":
        run_visualize()
    elif args.stage == "all":
        run_all()

if __name__ == "__main__":
    main()
