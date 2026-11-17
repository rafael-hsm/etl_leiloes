# Guia para Contribuidores

## Como Contribuir

Obrigado pelo interesse em contribuir com o projeto ETL Leilões!

## Configuração do Ambiente

1. Clone o repositório
2. Execute `bash setup.sh` para configurar o ambiente
3. Ative o ambiente virtual: `source .venv/bin/activate`

## Estrutura do Código

- **src/extract/**: Spiders Scrapy para extração de dados
- **src/transform/**: Scripts de transformação de dados
- **src/visualize/**: Dashboard Dash para visualização
- **config/**: Configurações centralizadas

## Padrões de Código

- Use Python 3.13
- Siga PEP 8
- Adicione docstrings em funções importantes
- Use configurações de `config/settings.py` em vez de hardcoded

## Testes

Antes de enviar um PR:
1. Execute os testes: `pytest tests/`
2. Verifique se o spider Scrapy funciona: `cd src && scrapy crawl parque_leiloes`
3. Verifique se a transformação funciona: `python3 src/transform/main.py`
4. Verifique se o dashboard funciona: `python3 src/visualize/app.py`

## Commit Messages

Use mensagens de commit claras e descritivas:
- `feat: adicionar novo filtro no dashboard`
- `fix: corrigir path do banco de dados`
- `docs: atualizar README`

## Pull Requests

1. Faça fork do projeto
2. Crie uma branch para sua feature: `git checkout -b feature/nova-feature`
3. Commit suas mudanças: `git commit -m 'feat: adicionar nova feature'`
4. Push para a branch: `git push origin feature/nova-feature`
5. Abra um Pull Request

## Issues

Ao reportar bugs:
- Descreva o problema claramente
- Inclua passos para reproduzir
- Inclua logs de erro relevantes
- Especifique seu ambiente (OS, Python version)
