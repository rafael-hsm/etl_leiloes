"""Testes de transformação"""
import sys
from pathlib import Path
import pandas as pd

# Adicionar o diretório config ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'config'))

def test_transform_module_exists():
    """Testa se o módulo de transformação pode ser importado"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'transform'))
        import main
        assert True
    except ImportError:
        assert False, "Não foi possível importar o módulo de transformação"

def test_dataframe_operations():
    """Testa operações básicas de DataFrame"""
    # Criar DataFrame de teste
    test_data = [
        {
            "titulo_lote": "Teste",
            "modelo": "Gol",
            "marca": "Volkswagen",
            "ano": "2020",
            "acessorios": ["Ar condicionado", "Direção elétrica"]
        }
    ]
    df = pd.DataFrame(test_data)
    
    # Testar conversão de acessórios
    if 'acessorios' in df.columns:
        df['acessorios'] = df['acessorios'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
    
    assert df['acessorios'].iloc[0] == "Ar condicionado, Direção elétrica"
    assert len(df) == 1

if __name__ == "__main__":
    test_transform_module_exists()
    test_dataframe_operations()
    print("Todos os testes de transformação passaram!")
