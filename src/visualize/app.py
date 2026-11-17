from dash import Dash, dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import pandas as pd
import sqlite3
import sys
import logging
from pathlib import Path

# Adicionar o diretório config ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'config'))
from settings import (
    SQLITE_DB_PATH, DB_TABLE_NAME, EDITAIS_TABLE_NAME,
    DASH_HOST, DASH_PORT, DASH_DEBUG, LOG_LEVEL, LOG_FORMAT,
)

# Configurar logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


# ===== Acesso ao banco =====

def query_df(sql, params=()):
    conn = sqlite3.connect(SQLITE_DB_PATH)
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def get_editais():
    return query_df(f"SELECT * FROM {EDITAIS_TABLE_NAME} ORDER BY id")


def get_edital(edital_id):
    return query_df(
        f"SELECT * FROM {EDITAIS_TABLE_NAME} WHERE id = ?", (edital_id,)
    )


def get_lotes(edital_id=None):
    if edital_id is None:
        return query_df(f"SELECT * FROM {DB_TABLE_NAME}")
    return query_df(
        f"SELECT * FROM {DB_TABLE_NAME} WHERE edital_id = ?", (edital_id,)
    )


# ===== Funções de dados =====

# Função para extrair o valor numérico de uma string de valor
def extract_value(valor):
    try:
        return float(valor.split(" ")[1].replace(".", "").replace(",", "."))
    except:
        return None


def prepare_df(df):
    """Adiciona colunas derivadas usadas em análises e filtros"""
    df = df.copy()
    df['valor_mercado_num'] = df['valor_mercado'].apply(extract_value)
    df['valor_ultimo_lance_num'] = df['valor último lance'].apply(extract_value)
    df['oportunidade'] = df['valor_mercado_num'] - df['valor_ultimo_lance_num']
    df['total lances'] = pd.to_numeric(df['total lances'], errors='coerce').fillna(0)
    return df


# Colunas exibidas na tabela principal
TABLE_COLUMNS = [
    'titulo_lote', 'categoria', 'modelo', 'marca', 'ano',
    'quilometragem', 'valor último lance', 'valor_mercado',
    'total lances', 'url_lote',
]

COLUMN_LABELS = {
    'titulo_lote': 'Lote',
    'categoria': 'Categoria',
    'modelo': 'Modelo',
    'marca': 'Marca',
    'ano': 'Ano',
    'quilometragem': 'KM',
    'valor último lance': 'Valor do Último Lance',
    'valor_mercado': 'Valor de Mercado',
    'total lances': 'Total de Lances',
    'url_lote': 'Link',
    'oportunidade': 'Oportunidade (R$)',
}

GRID_OPTIONS = {
    'defaultColDef': {
        'sortable': True,
        'filter': True,
        'resizable': True,
    },
    'pagination': True,
    'paginationPageSize': 15,
}


def make_column_defs(columns):
    return [
        {'field': col, 'headerName': COLUMN_LABELS.get(col, col)}
        for col in columns
    ]


def grid_row_data(frame, columns):
    """Converte DataFrame para rowData do AgGrid (sem NaN)"""
    records = frame[columns].where(pd.notna(frame[columns]), '').to_dict('records')
    return records


def status_badge(status):
    """Badge Bootstrap com cor conforme o status do edital"""
    s = str(status).lower()
    if 'online' in s or 'lances' in s:
        color = 'success'
    elif 'breve' in s:
        color = 'warning'
    elif 'encerrad' in s:
        color = 'secondary'
    else:
        color = 'info'
    return dbc.Badge(status, color=color, className='me-1')


# ===== Páginas =====

def home_layout():
    """Página inicial: lista os editais de veículos encontrados"""
    editais = get_editais()

    cards = []
    if editais.empty:
        cards.append(
            dbc.Col([
                dbc.Alert(
                    "Nenhum edital encontrado. Execute o pipeline ETL "
                    "(./setup.sh --etl) para atualizar os dados.",
                    color='warning',
                )
            ], width=12)
        )
    else:
        for _, ed in editais.iterrows():
            botoes = []
            if ed.get('url_detalhes'):
                botoes.append(
                    dbc.Button(
                        "Ver no site", href=ed['url_detalhes'],
                        color='outline-primary', size='sm', target='_blank',
                    )
                )
            if ed.get('url_edital'):
                botoes.append(
                    dbc.Button(
                        "Edital (PDF)", href=ed['url_edital'],
                        color='outline-secondary', size='sm', target='_blank',
                    )
                )
            botoes.append(
                dbc.Button(
                    "Analisar", href=f"/edital/{int(ed['id'])}",
                    color='primary', size='sm', className='ms-1',
                )
            )

            cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5(ed['nome'], className='mb-1'),
                            status_badge(ed['status']),
                        ]),
                        dbc.CardBody([
                            html.P(
                                [
                                    html.Strong("Data: "), ed['data'],
                                    html.Br(),
                                    html.Strong("Categoria: "), ed['categoria'],
                                ],
                                className='text-muted mb-3',
                            ),
                            dbc.ButtonGroup(botoes),
                        ]),
                    ], className='shadow-sm h-100')
                ], width=12, md=6, xl=4, className='mb-4')
            )

    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Leilões de Veículos", className="text-center mt-3"),
                html.P(
                    "Editais de veículos do Parque dos Leilões (Brasília/DF). "
                    "Clique em \"Analisar\" para ver os lotes e filtros.",
                    className="text-center text-muted",
                ),
            ], width=12),
        ]),
        dbc.Row(cards),
    ], fluid=True)


ANALYSIS_COLUMNS = ['titulo_lote', 'categoria', 'modelo', 'marca', 'ano',
                    'quilometragem', 'valor último lance', 'total lances', 'url_lote']


def _analyses_grids(df_edital):
    """Gera as 3 grades de análise para o edital selecionado"""
    mais_procurados = df_edital[df_edital['total lances'] > 9].sort_values(
        by='total lances', ascending=False)
    sem_lances = df_edital[df_edital['total lances'] == 0].sort_values(
        by='total lances', ascending=True)
    com_lances = df_edital.dropna(subset=['valor_ultimo_lance_num'])
    melhores = com_lances.sort_values(by='oportunidade', ascending=False)

    opts = {**GRID_OPTIONS, 'pagination': False}
    return [
        dbc.Row([
            dbc.Col([
                html.H4("Itens Mais Procurados", className="text-center"),
                dag.AgGrid(
                    id='mais-procurados-grid',
                    columnDefs=make_column_defs(ANALYSIS_COLUMNS),
                    rowData=grid_row_data(mais_procurados, ANALYSIS_COLUMNS),
                    dashGridOptions=opts,
                    style={'height': '320px'},
                ),
            ], width=12),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([
                html.H4("Itens Sem Lances", className="text-center"),
                dag.AgGrid(
                    id='sem-lances-grid',
                    columnDefs=make_column_defs(ANALYSIS_COLUMNS),
                    rowData=grid_row_data(sem_lances, ANALYSIS_COLUMNS),
                    dashGridOptions=opts,
                    style={'height': '320px'},
                ),
            ], width=12),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([
                html.H4("Melhores Negócios", className="text-center"),
                dag.AgGrid(
                    id='melhores-negocios-grid',
                    columnDefs=make_column_defs(ANALYSIS_COLUMNS + ['oportunidade']),
                    rowData=grid_row_data(melhores, ANALYSIS_COLUMNS + ['oportunidade']),
                    dashGridOptions=opts,
                    style={'height': '320px'},
                ),
            ], width=12),
        ]),
    ]


def edital_layout(edital_id):
    """Página de análise de um edital: filtros + grades dos lotes"""
    ed = get_edital(edital_id)
    if ed.empty:
        return dbc.Alert(f"Edital {edital_id} não encontrado.", color='danger')

    ed = ed.iloc[0]
    df_edital = prepare_df(get_lotes(edital_id))

    filtros = dbc.Card([
        dbc.CardHeader(html.H5("Filtros", className="mb-0")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Marca"),
                    dcc.Dropdown(
                        id='marca-dropdown',
                        options=[
                            {'label': m, 'value': m}
                            for m in sorted(df_edital['marca'].unique()) if m
                        ],
                        multi=True,
                        placeholder="Todas",
                    ),
                ], width=4),
                dbc.Col([
                    html.Label("Modelo"),
                    dcc.Dropdown(
                        id='modelo-dropdown',
                        options=[],
                        multi=True,
                        placeholder="Todos",
                    ),
                ], width=4),
                dbc.Col([
                    html.Label("Ano"),
                    dcc.Dropdown(
                        id='ano-dropdown',
                        options=[
                            {'label': a, 'value': a}
                            for a in sorted(df_edital['ano'].astype(str).unique()) if a
                        ],
                        multi=True,
                        placeholder="Todos",
                    ),
                ], width=4),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Label("Situação"),
                    dcc.Dropdown(
                        id='situacao-dropdown',
                        options=[
                            {'label': 'Todos', 'value': 'Todos'},
                            {'label': 'Com lances', 'value': 'Com lances'},
                            {'label': 'Sem lances', 'value': 'Sem lances'},
                        ],
                        value='Todos',
                        clearable=False,
                    ),
                ], width=4),
                dbc.Col([
                    html.Label("Valor do último lance mín. (R$)"),
                    dcc.Input(id='valor-min', type='number', min=0,
                              placeholder="Ex.: 10000"),
                ], width=4),
                dbc.Col([
                    html.Label("Valor do último lance máx. (R$)"),
                    dcc.Input(id='valor-max', type='number', min=0,
                              placeholder="Ex.: 50000"),
                ], width=4),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Button("Limpar filtros", id='clear-filters',
                               color='secondary', size='sm', className='mt-3'),
                ], width=12),
            ]),
        ]),
    ])

    grid = dbc.Card([
        dbc.CardHeader(html.H5("Lotes do Edital", className="mb-0")),
        dbc.CardBody([
            dag.AgGrid(
                id='leiloes-grid',
                columnDefs=make_column_defs(TABLE_COLUMNS),
                rowData=grid_row_data(df_edital, TABLE_COLUMNS),
                dashGridOptions=GRID_OPTIONS,
                style={'height': '500px'},
            ),
        ]),
    ])

    botoes_edital = []
    if ed.get('url_detalhes'):
        botoes_edital.append(
            dbc.Button("Ver no site", href=ed['url_detalhes'],
                       color='outline-primary', size='sm', target='_blank')
        )
    if ed.get('url_edital'):
        botoes_edital.append(
            dbc.Button("Edital (PDF)", href=ed['url_edital'],
                       color='outline-secondary', size='sm', target='_blank',
                       className='ms-1')
        )

    return dbc.Container([
        dcc.Store(id='edital-store', data=int(edital_id)),
        dbc.Row([
            dbc.Col([
                dcc.Link("← Voltar para editais", href="/",
                         className="text-decoration-none"),
                html.H3(ed['nome'], className="mt-2"),
                html.Div([
                    status_badge(ed['status']),
                    dbc.Badge(f"Data: {ed['data']}", color='light',
                              text_color='dark', className='me-1'),
                    dbc.Badge(f"Categoria: {ed['categoria']}", color='light',
                              text_color='dark'),
                ], className="my-2"),
                dbc.ButtonGroup(botoes_edital, className="mb-3"),
            ], width=12),
        ]),
        dbc.Row([dbc.Col(filtros, width=12)], className="mb-4"),
        dbc.Row([dbc.Col(grid, width=12)], className="mb-4"),
        *_analyses_grids(df_edital),
    ], fluid=True)


# ===== App e roteamento =====

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.MORPH],
    suppress_callback_exceptions=True,
)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
])


@callback(Output('page-content', 'children'), Input('url', 'pathname'))
def render_page(pathname):
    if pathname and pathname.startswith('/edital/'):
        try:
            edital_id = int(pathname.rstrip('/').split('/')[-1])
            return edital_layout(edital_id)
        except ValueError:
            pass
    return home_layout()


# ===== Callbacks da página de análise =====

def _empty(v):
    return v in (None, [], '')


@callback(
    Output('leiloes-grid', 'rowData'),
    Output('modelo-dropdown', 'options'),
    Input('edital-store', 'data'),
    Input('marca-dropdown', 'value'),
    Input('modelo-dropdown', 'value'),
    Input('ano-dropdown', 'value'),
    Input('situacao-dropdown', 'value'),
    Input('valor-min', 'value'),
    Input('valor-max', 'value'),
    prevent_initial_call=False,
)
def update_table(edital_id, marcas, modelos, anos, situacao, valor_min, valor_max):
    filtered = prepare_df(get_lotes(edital_id))

    if not _empty(marcas):
        filtered = filtered[filtered['marca'].isin(marcas)]
    if not _empty(modelos):
        filtered = filtered[filtered['modelo'].isin(modelos)]
    if not _empty(anos):
        filtered = filtered[filtered['ano'].astype(str).isin(anos)]
    if situacao == 'Com lances':
        filtered = filtered[filtered['total lances'] > 0]
    elif situacao == 'Sem lances':
        filtered = filtered[filtered['total lances'] == 0]
    if valor_min is not None:
        filtered = filtered[filtered['valor_ultimo_lance_num'] >= valor_min]
    if valor_max is not None:
        filtered = filtered[filtered['valor_ultimo_lance_num'] <= valor_max]

    modelo_options = [
        {'label': m, 'value': m}
        for m in sorted(filtered['modelo'].dropna().unique())
        if m
    ]

    return grid_row_data(filtered, TABLE_COLUMNS), modelo_options


@callback(
    Output('marca-dropdown', 'value'),
    Output('modelo-dropdown', 'value'),
    Output('ano-dropdown', 'value'),
    Output('situacao-dropdown', 'value'),
    Output('valor-min', 'value'),
    Output('valor-max', 'value'),
    Input('clear-filters', 'n_clicks'),
    prevent_initial_call=True,
)
def clear_all_filters(_):
    return None, None, None, 'Todos', None, None


# Executar o servidor
if __name__ == '__main__':
    logger.info(f"Iniciando servidor Dash em http://{DASH_HOST}:{DASH_PORT}")
    app.run(host=DASH_HOST, port=DASH_PORT, debug=DASH_DEBUG)
