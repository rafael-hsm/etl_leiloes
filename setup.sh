#!/bin/bash
#
# Script de execução do projeto ETL Leilões
#
# Uso:
#   ./setup.sh              Pipeline completo: setup (se necessário) + ETL + dashboard
#   ./setup.sh --setup      Apenas instala as dependências
#   ./setup.sh --etl        Executa extract + transform (sem dashboard)
#   ./setup.sh --visualize  Executa apenas o dashboard
#   ./setup.sh --run        ETL + dashboard (assume dependências instaladas)
#
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

VENV_DIR=".venv"
PYTHON="${PYTHON:-python3.13}"

# Ativa o venv se existir
activate_venv() {
    if [ -f "$VENV_DIR/bin/activate" ]; then
        # shellcheck disable=SC1091
        source "$VENV_DIR/bin/activate"
    else
        echo "Erro: ambiente virtual não encontrado em $VENV_DIR"
        echo "Execute: $PYTHON -m venv $VENV_DIR && source $VENV_DIR/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
}

setup_env() {
    echo "=== Configurando ambiente Python ==="

    if [ ! -d "$VENV_DIR" ]; then
        echo "Criando ambiente virtual com $PYTHON..."
        $PYTHON -m venv "$VENV_DIR" || python3 -m venv "$VENV_DIR"
    else
        echo "Ambiente virtual já existe, pulando criação."
    fi

    activate_venv

    echo "Instalando dependências..."
    pip install --upgrade pip
    pip install -r requirements.txt

    mkdir -p data
    echo "Setup concluído."
}

run_etl() {
    echo "=== Executando ETL (extract + transform) ==="
    activate_venv
    python3 scripts/run_etl.py all
}

run_visualize() {
    echo "=== Iniciando dashboard em http://127.0.0.1:8050/ ==="
    activate_venv
    python3 scripts/run_etl.py visualize
}

case "${1:-}" in
    --setup)
        setup_env
        ;;
    --etl)
        run_etl
        ;;
    --visualize|--dashboard)
        run_visualize
        ;;
    --run)
        run_etl
        run_visualize
        ;;
    ""|--all)
        setup_env
        run_etl
        run_visualize
        ;;
    -h|--help)
        sed -n '5,10p' "$0"
        ;;
    *)
        echo "Opção desconhecida: $1"
        echo "Use --help para ver as opções."
        exit 1
        ;;
esac
