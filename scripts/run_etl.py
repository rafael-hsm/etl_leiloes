#!/usr/bin/env python3
"""
Script de execução unificado para o pipeline ETL
Uso: python scripts/run_etl.py [extract|transform|visualize|all]
"""
import sys
import subprocess
import argparse
from pathlib import Path

def run_extract():
    """Executa a extração com Scrapy"""
    print("=== Iniciando Extração (Scrapy) ===")
    src_dir = Path(__file__).parent.parent / "src"
    result = subprocess.run(
        ["scrapy", "crawl", "parque_leiloes", "-O", "../data/data.json"],
        cwd=src_dir,
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print("ERROS:", result.stderr)
    if result.returncode == 0:
        print("✓ Extração concluída com sucesso")
    else:
        print("✗ Extração falhou")
        sys.exit(1)

def run_transform():
    """Executa a transformação JSON → SQLite"""
    print("=== Iniciando Transformação ===")
    result = subprocess.run(
        ["python3", "src/transform/main.py"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print("ERROS:", result.stderr)
    if result.returncode == 0:
        print("✓ Transformação concluída com sucesso")
    else:
        print("✗ Transformação falhou")
        sys.exit(1)

def run_visualize():
    """Executa o dashboard Dash"""
    print("=== Iniciando Dashboard ===")
    print("Acesse http://127.0.0.1:8050/ no navegador")
    result = subprocess.run(
        ["python3", "src/visualize/app.py"],
        text=True
    )
    if result.returncode != 0:
        print("✗ Dashboard falhou")
        sys.exit(1)

def run_all():
    """Executa o pipeline completo ETL"""
    print("=== Executando Pipeline ETL Completo ===")
    run_extract()
    run_transform()
    print("\n=== Pipeline ETL concluído ===")
    print("Para visualizar os dados, execute: python scripts/run_etl.py visualize")

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
