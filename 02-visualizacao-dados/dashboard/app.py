"""Dashboard interativo (Dash). Rodar com:  python app.py  e abrir http://127.0.0.1:8050"""
from dash import Dash, Input, Output, dcc, html

import dados
import graficos as g

TOTAL = dados.carregar()
PRECO_MIN, PRECO_MAX = 20, 340

app = Dash(__name__, title="E-commerce de moda · Dashboard")
server = app.server  # para publicar com gunicorn, se um dia for preciso


def cartao(chave: str, titulo: str) -> html.Div:
    return html.Div(className="cartao", children=[
        html.H2(titulo),
        html.P(id=f"leitura-{chave}", className="leitura"),
        dcc.Graph(id=f"graf-{chave}", config=g.CONFIG, style={"height": f"{g.ALTURA}px"}),
    ])


opcoes_publico = [{"label": p, "value": p} for p in [dados.TODOS, *dados.PUBLICOS]]

N_UNICOS = int((~TOTAL["Repetido"]).sum())
opcoes_repetidos = [
    {"label": html.Span(["Remover", html.Span(f"{N_UNICOS}", className="n")]), "value": "unicos"},
    {"label": html.Span(["Manter", html.Span(f"{len(TOTAL)}", className="n")]), "value": "todos"},
]

app.layout = html.Div(className="pagina", children=[
    html.Header(className="cabecalho", children=[
        html.H1("E-commerce de moda"),
        html.P("Preços, avaliações e vendas de um catálogo de produtos de moda. "
               "Exercício do curso de Analista de Dados da EBAC."),
    ]),

    html.Div(className="filtros", children=[
        html.Div(className="filtro-linha", children=[
            html.Div(className="filtro-grupo", children=[
                html.Span("Público", className="filtro-rotulo"),
                dcc.RadioItems(id="publico", options=opcoes_publico, value=dados.TODOS,
                               className="seg", inline=True),
            ]),
            html.Div(className="filtro-grupo filtro-preco", children=[
                html.Span("Faixa de preço (R$)", className="filtro-rotulo"),
                dcc.RangeSlider(id="preco", min=PRECO_MIN, max=PRECO_MAX, step=10, value=[PRECO_MIN, PRECO_MAX],
                                marks={v: str(v) for v in range(50, 350, 50)}, allowCross=False,
                                tooltip={"placement": "bottom", "always_visible": False}),
            ]),
        ]),
        html.Div(className="filtro-linha", children=[
            html.Div(className="filtro-grupo", children=[
                html.Span("Anúncios repetidos", className="filtro-rotulo"),
                dcc.RadioItems(id="repetidos", options=opcoes_repetidos, value="unicos",
                               className="seg", inline=True),
            ]),
        ]),
    ]),

    html.P(dados.nota_repetidos(TOTAL), className="nota"),

    html.Div(id="kpis", className="kpis"),
    html.Div(className="grade", children=[cartao(c, t) for c, t in g.CARTOES]),

    html.Div(className="cartao largo", children=[
        html.H2("Produtos que mais vendem"),
        html.P(className="leitura",
               children="Os dez primeiros da seleção, por vendas estimadas (mínimo da faixa). "
                        "É também a versão em texto dos gráficos."),
        html.Div(id="tabela", className="tabela-rolagem"),
    ]),

    html.Footer(className="rodape", children=[
        html.P("Vendas estimadas: o catálogo informa faixas (+100, +1000, +10mil…); aqui vale o limite inferior da faixa, "
               "então os totais são um mínimo."),
        html.P("Temas das avaliações: contagem por palavras-chave nas três avaliações de cada produto; "
               "mostra o que se comenta, não se é elogio ou crítica."),
        html.P("Marcas e públicos foram padronizados (ex.: “Stillger Jeans” e “Stillger” viram uma só); "
               "anúncios sem marca identificável ficam fora do ranking de marcas. "
               "Desconto lido como percentual. Base: ecommerce_estatistica.csv, de exercícios anteriores do curso."),
    ]),
])


def kpi(item: dict) -> html.Div:
    return html.Div(className="kpi", children=[
        html.Div(item["rotulo"], className="kpi-rotulo"),
        html.Div(item["valor"], className="kpi-valor"),
        html.Div(item["ref"], className="kpi-ref"),
    ])


def tabela(linhas: list[list[str]]) -> html.Table:
    numericas = set(g.COLUNAS_NUMERICAS)
    cab = html.Tr([html.Th(c, className="num" if i in numericas else "") for i, c in enumerate(g.CABECALHO_TABELA)])
    corpo = [html.Tr([html.Td(v, className="num" if i in numericas else "") for i, v in enumerate(l)]) for l in linhas]
    return html.Table([html.Thead(cab), html.Tbody(corpo)])


@app.callback(
    [Output("kpis", "children"), Output("tabela", "children")]
    + [Output(f"graf-{c}", "figure") for c, _ in g.CARTOES]
    + [Output(f"leitura-{c}", "children") for c, _ in g.CARTOES],
    Input("publico", "value"),
    Input("repetidos", "value"),
    Input("preco", "value"),
)
def atualizar(publico, repetidos, preco):
    base = dados.filtrar(TOTAL, unicos=(repetidos == "unicos"))   # catálogo na visão escolhida
    faixa = dados.filtrar(base, preco=tuple(preco))               # + faixa de preço
    df = dados.filtrar(faixa, publico)                            # + público
    figuras = g.todas_figuras(df, faixa, publico)
    textos = g.leituras(df, faixa, publico)
    return (
        [kpi(k) for k in dados.kpis(df, base)],
        tabela(g.linhas_tabela(df)),
        *[figuras[c] for c, _ in g.CARTOES],
        *[textos[c] for c, _ in g.CARTOES],
    )


if __name__ == "__main__":
    app.run(debug=False)
