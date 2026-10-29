"""Figuras e textos do dashboard. Cada função recebe o DataFrame já filtrado."""
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio

from dados import (PUBLICOS, SEM_MARCA, TEMAS, TODOS, compacto, decimal, inteiro, reais)

pio.templates.default = "none"

# ---------- paleta (azul = dado; tons neutros = estrutura) ----------
SUPERFICIE = "#fcfcfb"
TEXTO = "#0b0b0b"
TEXTO_2 = "#52514e"
TEXTO_MUDO = "#898781"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"
AZUL = "#2a78d6"
CINZA = "#b5b4ab"      # contexto / "não selecionado"
VERMELHO = "#e34948"   # polo negativo da escala divergente
NEUTRO = "#f0efec"     # ponto médio da escala divergente
FONTE = "system-ui, -apple-system, 'Segoe UI', sans-serif"

CONFIG = {
    "displaylogo": False,
    "displayModeBar": "hover",
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
}
ALTURA = 340

# (chave, título do cartão), na ordem em que aparecem
CARTOES = [
    ("hist", "Distribuição dos preços"),
    ("disp", "Preço × nota de avaliação"),
    ("marcas", "Marcas que mais vendem"),
    ("vpub", "Vendas por público"),
    ("publicos", "Preço por público"),
    ("corr", "Correlação entre as variáveis"),
    ("aval", "Avaliações por faixa de vendas"),
    ("temas", "O que as avaliações comentam"),
]
# vendas estimadas = limite inferior da faixa informada no catálogo (+100, +1000, +10mil…)
METRICA = dict(coluna="Qtd_Vendidos_Cod", de="das vendas estimadas", formato=compacto,
               hover="%{x:,.0f} unidades")


def _curto(texto: str, n: int = 60) -> str:
    return texto if len(texto) <= n else texto[: n - 1].rstrip() + "…"


def _base(fig: go.Figure, **extra) -> go.Figure:
    """Aparência comum: fundo da superfície, grade fina, tooltip limpo, separadores pt-BR."""
    fig.update_layout(
        height=ALTURA,
        margin=dict(l=8, r=16, t=8, b=8),
        paper_bgcolor=SUPERFICIE,
        plot_bgcolor=SUPERFICIE,
        font=dict(family=FONTE, size=12, color=TEXTO_2),
        hoverlabel=dict(bgcolor="#ffffff", bordercolor=GRADE, font=dict(family=FONTE, size=12, color=TEXTO)),
        showlegend=False,
        separators=",.",
        **extra,
    )
    eixo = dict(
        linecolor=EIXO, gridcolor=GRADE, gridwidth=1, zeroline=False, ticks="",
        tickfont=dict(color=TEXTO_MUDO, size=11), title_font=dict(color=TEXTO_2, size=12),
        automargin=True,
    )
    fig.update_xaxes(**eixo)
    fig.update_yaxes(**eixo)
    return fig


def _vazio() -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text="Nenhum produto nesta seleção", showarrow=False, xref="paper", yref="paper",
        x=0.5, y=0.5, font=dict(size=13, color=TEXTO_MUDO),
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _base(fig)


# ---------- 1. distribuição de preços ----------

def hist_precos(df):
    if df.empty:
        return _vazio()
    passo = 20
    bordas = np.arange(20, 341, passo)
    contagem, _ = np.histogram(df["Preço"], bins=bordas)
    fig = go.Figure(go.Bar(
        x=bordas[:-1] + passo / 2, y=contagem, width=passo * 0.88,
        marker=dict(color=AZUL),
        customdata=np.column_stack([bordas[:-1], bordas[1:]]),
        hovertemplate="<b>%{y} produtos</b><br>R$ %{customdata[0]:.0f} a R$ %{customdata[1]:.0f}<extra></extra>",
    ))
    mediana = df["Preço"].median()
    fig.add_shape(type="line", x0=mediana, x1=mediana, y0=0, y1=1, yref="paper",
                  line=dict(color=TEXTO, width=2))
    a_direita = mediana < 230
    fig.add_annotation(
        x=mediana, y=1, yref="paper", showarrow=False, text=f"Mediana {reais(mediana, 0)}",
        xanchor="left" if a_direita else "right", xshift=8 if a_direita else -8, yanchor="top",
        font=dict(color=TEXTO, size=12),
    )
    _base(fig, bargap=0, barcornerradius=4)
    fig.update_xaxes(title="Preço (R$)", range=[20, 340], tick0=0, dtick=50, tickprefix="R$ ", showgrid=False)
    fig.update_yaxes(title="Produtos", range=[0, contagem.max() * 1.2])
    return fig


# ---------- 2. preço x nota ----------

def disp_preco_nota(df):
    if df.empty:
        return _vazio()
    fig = go.Figure(go.Scatter(
        x=df["Preço"], y=df["Nota"], mode="markers",
        marker=dict(size=9, color=AZUL, opacity=0.7, line=dict(color=SUPERFICIE, width=1.5)),
        customdata=np.column_stack([df["Título"].map(_curto), df["Marca"]]),
        hovertemplate="<b>Nota %{y:.1f}</b> · R$ %{x:.2f}<br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>",
    ))
    _base(fig, hoverdistance=30)
    fig.update_xaxes(title="Preço (R$)", range=[0, 350], tick0=0, dtick=50, tickprefix="R$ ")
    fig.update_yaxes(title="Nota média (0 a 5)", range=[2.1, 5.2], dtick=0.5, tickformat=".1f")
    return fig


# ---------- 3. marcas que mais vendem  ----------

def barras_marcas(df):
    m = METRICA
    com_marca = df[df["Marca"] != SEM_MARCA]
    if com_marca.empty:
        return _vazio()
    total = com_marca[m["coluna"]].sum()
    top = (com_marca.groupby("Marca")
                    .agg(valor=(m["coluna"], "sum"), produtos=("Título", "count"))
                    .sort_values("valor", ascending=False).head(10))
    top.index = [_curto(nome, 22) for nome in top.index]
    fig = go.Figure(go.Bar(
        y=top.index, x=top["valor"], orientation="h", marker=dict(color=AZUL),
        text=[m["formato"](v) for v in top["valor"]], textposition="outside", cliponaxis=False,
        textfont=dict(color=TEXTO_2, size=12),
        customdata=np.column_stack([top["valor"] / total, top["produtos"]]),
        hovertemplate=("<b>%{y}</b><br>" + m["hover"] + " (mín.)<br>"
                       "%{customdata[0]:.1%} do total · %{customdata[1]} produtos<extra></extra>"),
    ))
    _base(fig, bargap=0.45, barcornerradius=4)
    fig.update_xaxes(visible=False, range=[0, top["valor"].max() * 1.25])
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(color=TEXTO_2, size=12))
    return fig


# ---------- 4. vendas por público (o selecionado em destaque) ----------

def barras_publico(total, selecionado=TODOS):
    """Soma por público; ignora o filtro de público e destaca o escolhido."""
    m = METRICA
    soma = total.groupby("Público")[m["coluna"]].sum().reindex(PUBLICOS).fillna(0)
    contagem = total.groupby("Público").size().reindex(PUBLICOS).fillna(0).astype(int)
    if soma.sum() == 0:
        return _vazio()
    nomes = [f"{p}  ·  {contagem[p]}" for p in PUBLICOS]
    cores = [AZUL if selecionado in (TODOS, p) else CINZA for p in PUBLICOS]
    fig = go.Figure(go.Bar(
        y=nomes, x=soma.values, orientation="h", marker=dict(color=cores),
        text=[m["formato"](v) for v in soma.values], textposition="outside", cliponaxis=False,
        textfont=dict(color=TEXTO_2, size=12),
        customdata=soma.values / soma.sum(),
        hovertemplate="<b>%{y}</b><br>" + m["hover"] + " (mín.)<br>%{customdata:.1%} do total<extra></extra>",
    ))
    _base(fig, bargap=0.55, barcornerradius=4)
    fig.update_xaxes(visible=False, range=[0, soma.max() * 1.25])
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(color=TEXTO_2, size=12))
    return fig


# ---------- 5. preço por público (o selecionado em destaque) ----------

def box_publicos(total, selecionado=TODOS):
    """Compara os quatro públicos; ignora o filtro de público e destaca o escolhido."""
    fig = go.Figure()
    nomes, medianas, cores, dados_hover, rotulos = [], [], [], [], []
    for p in PUBLICOS:
        preco = total.loc[total["Público"] == p, "Preço"]
        if preco.empty:
            continue
        nome = f"{p}  ·  {len(preco)}"
        cor = AZUL if selecionado in (TODOS, p) else CINZA
        q1, med, q3 = preco.quantile([0.25, 0.5, 0.75])
        fim = preco[preco <= q3 + 1.5 * (q3 - q1)].max()
        fig.add_trace(go.Box(
            x=preco, y=[nome] * len(preco), orientation="h", width=0.3, boxpoints=False,
            line=dict(color=cor, width=2), fillcolor=cor + "33",
            hoverinfo="skip",
        ))
        nomes.append(nome); medianas.append(med); cores.append(cor)
        dados_hover.append([q1, q3, preco.min(), preco.max(), len(preco)])
        rotulos.append((fim, f"  Mediana {reais(med, 0)}"))
    if not nomes:
        return _vazio()
    fig.add_trace(go.Scatter(
        x=medianas, y=nomes, mode="markers",
        marker=dict(size=10, color=cores, line=dict(color=SUPERFICIE, width=2)),
        customdata=dados_hover,
        hovertemplate=("<b>Mediana R$ %{x:.2f}</b><br>50% dos produtos entre R$ %{customdata[0]:.0f} e R$ %{customdata[1]:.0f}"
                       "<br>Mín. R$ %{customdata[2]:.0f} · máx. R$ %{customdata[3]:.0f}<extra></extra>"),
    ))
    fig.add_trace(go.Scatter(
        x=[r[0] for r in rotulos], y=nomes, mode="text", text=[r[1] for r in rotulos],
        textposition="middle right", textfont=dict(color=TEXTO_2, size=12), hoverinfo="skip",
    ))
    _base(fig)
    fig.update_xaxes(title="Preço (R$)", range=[0, 470], tick0=0, dtick=100, tickprefix="R$ ")
    fig.update_yaxes(categoryorder="array", categoryarray=nomes, autorange="reversed",
                     showgrid=False, tickfont=dict(color=TEXTO_2, size=12))
    return fig


# ---------- 6. correlação ----------

ROTULOS_CORR = {
    "Nota": "Nota", "N_Avaliações": "Nº de avaliações", "Desconto": "Desconto",
    "Preço": "Preço", "Qtd_Vendidos_Cod": "Vendas (mín.)",
}


def heat_correlacao(df):
    if len(df) < 3:
        return _vazio()
    nomes = list(ROTULOS_CORR.values())
    z = df[list(ROTULOS_CORR)].corr().to_numpy()
    fig = go.Figure(go.Heatmap(
        z=z, x=nomes, y=nomes, zmin=-1, zmax=1, xgap=2, ygap=2,
        colorscale=[[0, VERMELHO], [0.5, NEUTRO], [1, AZUL]],
        colorbar=dict(thickness=10, len=0.85, outlinewidth=0, tickvals=[-1, 0, 1],
                      tickfont=dict(color=TEXTO_MUDO, size=11)),
        hovertemplate="<b>%{y} × %{x}</b><br>r = %{z:.2f}<extra></extra>",
    ))
    for i, linha in enumerate(z):
        for j, v in enumerate(linha):
            fig.add_annotation(
                x=nomes[j], y=nomes[i], showarrow=False,
                text="—" if np.isnan(v) else decimal(v),
                font=dict(size=12, color="#ffffff" if abs(np.nan_to_num(v)) > 0.55 else TEXTO),
            )
    _base(fig)
    fig.update_xaxes(showgrid=False, linecolor=SUPERFICIE, side="bottom")
    fig.update_yaxes(showgrid=False, linecolor=SUPERFICIE, autorange="reversed")
    return fig


# ---------- 7. avaliações por faixa de vendas ----------

def box_avaliacoes(df):
    """Uma caixa por faixa de vendas, em escala log: não há reta forçada sobre dados em degraus."""
    if df.empty:
        return _vazio()
    faixas = (df.groupby("Qtd_Vendidos_Cod")
                .agg(faixa=("Qtd_Vendidos", "first"), n=("Título", "size"))
                .sort_index())
    fig = go.Figure()
    nomes, medianas, hover = [], [], []
    for cod, linha in faixas.iterrows():
        sub = df[df["Qtd_Vendidos_Cod"] == cod]
        nome = f"{linha['faixa']}<br>n = {linha['n']}"
        fig.add_trace(go.Box(
            y=sub["N_Avaliações"], x=[nome] * len(sub), width=0.5,
            boxpoints="all", jitter=0.45, pointpos=0, hoveron="points",
            marker=dict(size=8, color=AZUL, opacity=0.5, line=dict(color=SUPERFICIE, width=1.5)),
            line=dict(color=AZUL, width=2), fillcolor=AZUL + "1f",
            customdata=sub["Título"].map(_curto),
            hovertemplate="<b>%{y:,.0f} avaliações</b><br>%{customdata}<extra></extra>",
        ))
        nomes.append(nome)
        medianas.append(sub["N_Avaliações"].median())
        hover.append([linha["faixa"], linha["n"]])
    fig.add_trace(go.Scatter(
        x=nomes, y=medianas, mode="markers", customdata=hover,
        marker=dict(symbol="diamond", size=10, color=TEXTO, line=dict(color=SUPERFICIE, width=2)),
        hovertemplate="<b>Mediana: %{y:,.0f} avaliações</b><br>Faixa %{customdata[0]} · %{customdata[1]} produtos<extra></extra>",
    ))
    _base(fig, hoverdistance=30)
    fig.update_xaxes(title="Faixa de vendas do anúncio (n = produtos)", categoryorder="array",
                     categoryarray=nomes, showgrid=False)
    fig.update_yaxes(title="Nº de avaliações (escala log)", type="log",
                     tickvals=[3, 10, 100, 1000, 10000], ticktext=["3", "10", "100", "1 mil", "10 mil"])
    return fig


# ---------- 8. temas das avaliações ----------

def barras_temas(df):
    if df.empty:
        return _vazio()
    n_avaliacoes = 3 * len(df)
    contagem = {tema: int(df[f"Tema: {tema}"].sum()) for tema in TEMAS}
    ordem = sorted(contagem, key=contagem.get, reverse=True)
    parte = [contagem[t] / n_avaliacoes for t in ordem]
    fig = go.Figure(go.Bar(
        y=ordem, x=parte, orientation="h", marker=dict(color=AZUL),
        text=[f"{v:.0%}" for v in parte], textposition="outside", cliponaxis=False,
        textfont=dict(color=TEXTO_2, size=12),
        customdata=[[contagem[t], n_avaliacoes] for t in ordem],
        hovertemplate="<b>%{y}</b><br>%{x:.1%} das avaliações (%{customdata[0]} de %{customdata[1]})<extra></extra>",
    ))
    _base(fig, bargap=0.5, barcornerradius=4)
    fig.update_xaxes(visible=False, range=[0, max(parte) * 1.25 if max(parte) else 1])
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(color=TEXTO_2, size=12))
    return fig


# ---------- leituras (uma frase por gráfico, calculada sobre a seleção) ----------

def _forca(r: float) -> str:
    a = abs(r)
    grau = "praticamente nula" if a < 0.1 else "fraca" if a < 0.3 else "moderada" if a < 0.6 else "forte"
    if a < 0.1:
        return grau
    return f"{grau} ({'positiva' if r > 0 else 'negativa'})"


def leituras(df, total, selecionado=TODOS):
    chaves = [c for c, _ in CARTOES]
    if df.empty:
        return {c: "Sem produtos nesta seleção." for c in chaves}
    m = METRICA
    aviso = f" Amostra pequena (n = {len(df)})." if len(df) < 50 else ""

    q1, med, q3 = df["Preço"].quantile([0.25, 0.5, 0.75])
    r_pn = df["Preço"].corr(df["Nota"])

    com_marca = df[df["Marca"] != SEM_MARCA]
    sem_marca = len(df) - len(com_marca)
    if com_marca.empty:
        marcas = "Nenhum produto com marca definida nesta seleção."
    else:
        v = com_marca.groupby("Marca")[m["coluna"]].sum().sort_values(ascending=False)
        marcas = (f"{v.index[0]} responde por {v.iloc[0] / v.sum():.0%} {m['de']} entre as marcas identificadas; "
                  f"as três maiores somam {v.head(3).sum() / v.sum():.0%}.")
        if sem_marca:
            marcas += f" {sem_marca} produtos sem marca definida ficam fora do ranking."

    por_publico = total.groupby("Público")[m["coluna"]].sum()
    lider = por_publico.idxmax()
    vpub = f"{lider} concentra {por_publico.max() / por_publico.sum():.0%} {m['de']} (mín.)."

    medianas = total.groupby("Público")["Preço"].median().sort_values()

    corr = df[list(ROTULOS_CORR)].corr()
    rotulos = list(ROTULOS_CORR.values())
    pares = sorted(
        ((abs(corr.iloc[i, j]), corr.iloc[i, j], rotulos[i], rotulos[j])
         for i in range(5) for j in range(i + 1, 5) if not np.isnan(corr.iloc[i, j])),
        reverse=True,
    )
    corr_txt = "Poucos produtos para calcular correlações."
    if pares:
        corr_txt = f"Maior correlação: {pares[0][2]} × {pares[0][3]} ({decimal(pares[0][1])})."
        if len(pares) > 1:
            corr_txt += f" A segunda maior é {decimal(pares[1][1])}."
        corr_txt += aviso

    faixas = df.groupby("Qtd_Vendidos_Cod").agg(faixa=("Qtd_Vendidos", "first"),
                                                mediana=("N_Avaliações", "median")).sort_index()
    rho = df["N_Avaliações"].corr(df["Qtd_Vendidos_Cod"], method="spearman")
    if len(faixas) < 2 or np.isnan(rho):
        aval = "Poucas faixas de vendas para comparar." + aviso
    else:
        aval = (f"A mediana de avaliações vai de {inteiro(faixas['mediana'].iloc[0])} (faixa {faixas['faixa'].iloc[0]}) "
                f"a {inteiro(faixas['mediana'].iloc[-1])} (faixa {faixas['faixa'].iloc[-1]}); "
                f"correlação de postos de {decimal(rho)}.{aviso}")

    n_av = 3 * len(df)
    partes = sorted(((int(df[f"Tema: {t}"].sum()) / n_av, t) for t in TEMAS), reverse=True)
    temas = (f"{partes[0][1]} é o tema mais citado ({partes[0][0]:.0%} das avaliações), seguido de "
             f"{partes[1][1].lower()} ({partes[1][0]:.0%}). Mostra o que se comenta, não se é elogio ou crítica.")

    return {
        "hist": f"Metade dos produtos custa entre {reais(q1, 0)} e {reais(q3, 0)}; a mediana é {reais(med, 0)}.",
        "disp": ("Poucos produtos para calcular a correlação." if np.isnan(r_pn) else
                 f"Correlação de {decimal(r_pn)}: relação {_forca(r_pn)} entre preço e nota.{aviso}"),
        "marcas": marcas,
        "vpub": vpub,
        "publicos": (f"Maior mediana de preço: {medianas.index[-1]} ({reais(medianas.iloc[-1], 0)}); "
                     f"menor: {medianas.index[0]} ({reais(medianas.iloc[0], 0)})."),
        "corr": corr_txt,
        "aval": aval,
        "temas": temas,
    }


# ---------- tabela ----------

CABECALHO_TABELA = ["Produto", "Marca", "Público", "Preço", "Desconto", "Nota", "Avaliações",
                    "Vendas (faixa)"]
COLUNAS_NUMERICAS = (3, 4, 5, 6)


def linhas_tabela(df, n=10):
    top = df.sort_values([METRICA["coluna"], "N_Avaliações"], ascending=False).head(n)
    return [
        [_curto(r["Título"], 62), r["Marca"], r["Público"], reais(r["Preço"]), decimal(r["Desconto"], 0) + "%",
         decimal(r["Nota"], 1), inteiro(r["N_Avaliações"]), r["Qtd_Vendidos"]]
        for _, r in top.iterrows()
    ]


def todas_figuras(df, total, selecionado=TODOS):
    """Os oito gráficos, na ordem em que aparecem no dashboard."""
    return {
        "hist": hist_precos(df),
        "disp": disp_preco_nota(df),
        "marcas": barras_marcas(df),
        "vpub": barras_publico(total, selecionado),
        "publicos": box_publicos(total, selecionado),
        "corr": heat_correlacao(df),
        "aval": box_avaliacoes(df),
        "temas": barras_temas(df),
    }
