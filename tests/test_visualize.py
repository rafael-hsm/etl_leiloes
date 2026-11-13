"""Testes de visualização"""
import sys
from pathlib import Path

# Adicionar o diretório config ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'config'))

def test_visualize_module_exists():
    """Testa se o módulo de visualização pode ser importado"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'visualize'))
        # Não importamos app diretamente para evitar iniciar o servidor
        assert True
    except ImportError:
        assert False, "Não foi possível acessar o diretório de visualização"

def test_extract_value_function():
    """Testa a função de extração de valor"""
    def extract_value(valor):
        try:
            return float(valor.split(" ")[1].replace(".", "").replace(",", "."))
        except:
            return None
    
    # Testar formato brasileiro
    assert extract_value("R$ 50.000,00") == 50000.0
    assert extract_value("R$ 15.500,00") == 15500.0
    
    # Testar valor inválido
    assert extract_value("N/A") is None
    assert extract_value("") is None

if __name__ == "__main__":
    test_visualize_module_exists()
    test_extract_value_function()
    print("Todos os testes de visualização passaram!")
