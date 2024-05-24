from dash import Dash, dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import sqlite3

# Função para conectar ao banco de dados SQLite e carregar os dados
def load_data():
    conn = sqlite3.connect('/home/r4f43l/pessoal/etl_leiloes/data/etl_leiloes.db')
    df = pd.read_sql_query("SELECT * FROM parque_leiloes_items", conn)
    conn.close()
    return df

df = load_data()

# Função para extrair o valor numérico de uma string de valor
def extract_value(valor):
    try:
        return float(valor.split(" ")[1].replace(".", "").replace(",", "."))
    except:
        return None

# Função para transformar URLs em links markdown
def make_clickable(val):
    return f"[Link]({val})"



# Adicionar colunas de análise
df['valor_mercado_num'] = df['valor_mercado'].apply(extract_value)
df['valor_ultimo_lance_num'] = df['valor último lance'].apply(extract_value)
df['oportunidade'] = df['valor_mercado_num'] - df['valor_ultimo_lance_num']

# Aplicar a função make_clickable para a coluna url_lote
df['url_lote'] = df['url_lote'].apply(make_clickable)

# Filtrar carros que tiveram lances
df_com_lances = df.dropna(subset=['valor_ultimo_lance_num'])

# Carros mais procurados (ordenar por total de lances, mais de 9 lances)
carros_mais_procurados = df[df['total lances'] > 9].sort_values(by='total lances', ascending=False)

# Carros menos procurados (sem lances)
carros_menos_procurados = df[df['total lances'] == 0].sort_values(by='total lances', ascending=True)

# Melhores negócios fechados (ordenar pela maior diferença entre valor de mercado e valor do último lance)
melhores_negocios_fechados = df_com_lances.sort_values(by='oportunidade', ascending=False)

# Inicializar o aplicativo Dash com um tema Bootstrap
app = Dash(__name__, external_stylesheets=[dbc.themes.MORPH])

# Layout do aplicativo
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("Análises", className="text-center")
        ], width=12),
    ]),
    dbc.Row([
        dbc.Col([
            html.H4("Carros Mais Procurados", className="text-center"),
            html.P("Esta análise mostra os carros que receberam mais de 9 lances, indicando alta demanda."),
            dash_table.DataTable(
                id='mais-procurados-table',
                columns=[
                    {"name": "Marca", "id": "marca"},
                    {"name": "Modelo", "id": "modelo"},
                    {"name": "Ano", "id": "ano"},
                    {"name": "KM", "id": "quilometragem"},
                    {"name": "Valor do Último Lance", "id": "valor último lance"},
                    {"name": "Total de Lances", "id": "total lances"},
                    {"name": "Link", "id": "url_lote", "presentation": "markdown"}
                ],
                data=carros_mais_procurados.to_dict('records'),
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left'}
            )
        ], width=12),
    ]),
    dbc.Row([
        dbc.Col([
            html.H4("Carros Sem Lances", className="text-center"),
            html.P("Esta análise mostra os carros que não receberam nenhum lance."),
            dash_table.DataTable(
                id='menos-procurados-table',
                columns=[
                    {"name": "Modelo", "id": "modelo"},
                    {"name": "Marca", "id": "marca"},
                    {"name": "Ano", "id": "ano"},
                    {"name": "KM", "id": "quilometragem"},
                    {"name": "Valor do Último Lance", "id": "valor último lance"},
                    {"name": "Link", "id": "url_lote", "presentation": "markdown"}
                ],
                data=carros_menos_procurados.to_dict('records'),
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left'}
            )
        ], width=12),
    ]),
    dbc.Row([
        dbc.Col([
            html.H4("Melhores Negócios", className="text-center"),
            html.P("Esta análise mostra os melhores negócios até o momento, calculando a diferença entre o valor de mercado e o valor do último lance. TAXAS NÃO INCLUSAS!!!"),
            dash_table.DataTable(
                id='melhores-negocios-table',
                columns=[
                    {"name": "Modelo", "id": "modelo"},
                    {"name": "Marca", "id": "marca"},
                    {"name": "Ano", "id": "ano"},
                    {"name": "KM", "id": "quilometragem"},
                    {"name": "Valor do Último Lance", "id": "valor último lance"},
                    {"name": "Valor de Mercado", "id": "valor_mercado"},
                    {"name": "Oportunidade", "id": "oportunidade", "type": "numeric"},
                    {"name": "Link", "id": "url_lote", "presentation": "markdown"}
                ],
                data=melhores_negocios_fechados.to_dict('records'),
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left'}
            )
        ], width=12),
    ]),
    dbc.Row([
        dbc.Col([
            html.H2("Filtros"),
            html.Label("Marca do Carro"),
            dcc.Dropdown(
                id='marca-dropdown',
                options=[{'label': marca, 'value': marca} for marca in df['marca'].unique()],
                multi=True
            ),
            html.Label("Modelo do Carro"),
            dcc.Dropdown(
                id='modelo-dropdown',
                options=[{'label': modelo, 'value': modelo} for modelo in df['modelo'].unique()],
                multi=True
            )
        ], width=3),
        dbc.Col([
            html.H2("Tabela de Leilões"),
            dash_table.DataTable(
                id='leiloes-table',
                columns=[
                    {"name": "Modelo", "id": "modelo"},
                    {"name": "Marca", "id": "marca"},
                    {"name": "Ano", "id": "ano"},
                    {"name": "KM", "id": "quilometragem", "type": "numeric"},
                    {"name": "Valor do Último Lance", "id": "valor último lance"},
                    {"name": "Valor de Mercado", "id": "valor_mercado"},
                    {"name": "Total de Lances", "id": "total lances"}
                ],
                data=[],
                filter_action="native",
                sort_action="native",
                page_action="native",
                page_current=0,
                page_size=10,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left'},
                style_data_conditional=[
                    {'if': {'column_id': 'quilometragem'},
                     'textAlign': 'right'}
                ]
            )
        ], width=9)
    ])
], fluid=True, className="dbc")

# Callback para atualizar as opções do dropdown e a tabela com base nos filtros
@app.callback(
    [Output('modelo-dropdown', 'options'),
     Output('leiloes-table', 'data')],
    [Input('marca-dropdown', 'value'),
     Input('modelo-dropdown', 'value')]
)
def update_table(selected_marcas, selected_modelos):
    df = load_data()
    filtered_df = df

    if selected_marcas:
        filtered_df = filtered_df[filtered_df['marca'].isin(selected_marcas)]
    
    if selected_modelos:
        filtered_df = filtered_df[filtered_df['modelo'].isin(selected_modelos)]

    # Formatando a quilometragem
    filtered_df.loc[:, 'quilometragem'] = filtered_df['quilometragem'].apply(lambda x: f"{int(float(x)):,}".replace(",", ".") if x != '-' else '-')

    modelo_options = [{'label': modelo, 'value': modelo} for modelo in filtered_df['modelo'].unique()]

    return modelo_options, filtered_df.to_dict('records')

# Executar o servidor
if __name__ == '__main__':
    app.run_server(debug=True)
