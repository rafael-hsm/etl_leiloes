"""Configuração global dos testes"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent

# Adicionar diretórios ao path
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / 'config'))
sys.path.insert(0, str(ROOT_DIR / 'src'))
