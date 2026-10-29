"""Gera um HTML único e estático do dashboard (sem servidor), com os filtros de público,
faixa de preço e anúncios repetidos no próprio navegador.

    python exportar_html.py              # dashboard.html (carrega o Plotly de um CDN)
    python exportar_html.py --offline    # dashboard.html com o Plotly embutido (~5 MB)

Como não há servidor, todas as combinações de filtro são calculadas aqui e embutidas na página.
Gráficos idênticos em combinações diferentes são guardados uma única vez. Na versão Dash (app.py)
a faixa de preço é um controle deslizante; aqui são cinco faixas fixas.
"""
import argparse
import hashlib
import json
from html import escape
from pathlib import Path

import plotly.io as pio
from plotly.offline import get_plotlyjs, get_plotlyjs_version

import dados
import graficos as g

PASTA = Path(__file__).resolve().parent
# Faixas fixas de preço da versão estática (o limite superior de uma faixa não repete o início da seguinte).
FAIXAS = [
    ("todas", "Todas", None),
    ("f1", "Até R$ 75", (0, 75)),
    ("f2", "R$ 75 a 150", (75.01, 150)),
    ("f3", "R$ 150 a 225", (150.01, 225)),
    ("f4", "Acima de R$ 225", (225.01, 1e9)),
]


def calcular_estado(total, faixa, publico, unicos, pool):
    base = dados.filtrar(total, unicos=unicos)
    na_faixa = dados.filtrar(base, preco=faixa)
    df = dados.filtrar(na_faixa, publico)
    figs = {}
    for chave, fig in g.todas_figuras(df, na_faixa, publico).items():
        texto = pio.to_json(fig)
        h = hashlib.md5(texto.encode("utf-8")).hexdigest()[:10]
        pool.setdefault(h, json.loads(texto))
        figs[chave] = h
    return {
        "kpis": dados.kpis(df, base),
        "leituras": g.leituras(df, na_faixa, publico),
        "figs": figs,
        "tabela": g.linhas_tabela(df),
    }


def montar_pagina(total, offline):
    pool, estados = {}, {}
    for fid, _, faixa in FAIXAS:
        for p in [dados.TODOS, *dados.PUBLICOS]:
            for u in (True, False):
                estados[f"{fid}|{p}|{'u' if u else 't'}"] = calcular_estado(total, faixa, p, u, pool)
    n_unicos = int((~total["Repetido"]).sum())
    plotly = (f"<script>{get_plotlyjs()}</script>" if offline else
              f'<script src="https://cdn.plot.ly/plotly-{get_plotlyjs_version()}.min.js" charset="utf-8"></script>')
    botoes_publico = "".join(
        f'<button type="button" data-valor="{escape(p)}" aria-pressed="false">{escape(p)}</button>'
        for p in [dados.TODOS, *dados.PUBLICOS])
    botoes_faixa = "".join(
        f'<button type="button" data-valor="{fid}" aria-pressed="false">{escape(rot)}</button>'
        for fid, rot, _ in FAIXAS)
    cartoes = "".join(
        f'<div class="cartao"><h2>{escape(t)}</h2><p class="leitura" id="leitura-{c}"></p>'
        f'<div id="{c}" style="height:{g.ALTURA}px"></div></div>'
        for c, t in g.CARTOES)
    cabecalho_tabela = "".join(
        f'<th class="{"num" if i in g.COLUNAS_NUMERICAS else ""}">{escape(c)}</th>'
        for i, c in enumerate(g.CABECALHO_TABELA))
    css = (PASTA / "assets" / "estilo.css").read_text(encoding="utf-8")
    dados_json = json.dumps({"estados": estados, "figuras": pool}, ensure_ascii=False,
                            separators=(",", ":")).replace("</", "<\\/")

    return (MODELO
            .replace("__CSS__", css)
            .replace("__PLOTLY__", plotly)
            .replace("__BOTOES_PUBLICO__", botoes_publico)
            .replace("__BOTOES_FAIXA__", botoes_faixa)
            .replace("__CHAVES__", json.dumps([c for c, _ in g.CARTOES]))
            .replace("__NUMERICAS__", json.dumps(list(g.COLUNAS_NUMERICAS)))
            .replace("__N_UNICOS__", str(n_unicos))
            .replace("__N_TOTAL__", str(len(total)))
            .replace("__NOTA__", escape(dados.nota_repetidos(total)))
            .replace("__CARTOES__", cartoes)
            .replace("__CABECALHO_TABELA__", cabecalho_tabela)
            .replace("__CONFIG__", json.dumps(g.CONFIG))
            .replace("__DADOS__", dados_json))


MODELO = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>E-commerce de moda · Dashboard</title>
<style>
__CSS__
</style>
__PLOTLY__
</head>
<body>
<div class="pagina">
  <header class="cabecalho">
    <h1>E-commerce de moda</h1>
    <p>Preços, avaliações e vendas de um catálogo de produtos de moda. Exercício do curso de Analista de Dados da EBAC.</p>
  </header>

  <div class="filtros">
    <div class="filtro-linha">
      <div class="filtro-grupo">
        <span class="filtro-rotulo">Público</span>
        <div class="seg" id="seg-publico">__BOTOES_PUBLICO__</div>
      </div>
      <div class="filtro-grupo">
        <span class="filtro-rotulo">Faixa de preço</span>
        <div class="seg" id="seg-faixa">__BOTOES_FAIXA__</div>
      </div>
    </div>
    <div class="filtro-linha">
      <div class="filtro-grupo">
        <span class="filtro-rotulo">Anúncios repetidos</span>
        <div class="seg" id="seg-repetidos">
          <button type="button" data-valor="u" aria-pressed="true">Remover<span class="n">__N_UNICOS__</span></button>
          <button type="button" data-valor="t" aria-pressed="false">Manter<span class="n">__N_TOTAL__</span></button>
        </div>
      </div>
    </div>
  </div>
  <p class="nota">__NOTA__</p>

  <div class="kpis" id="kpis"></div>
  <div class="grade">__CARTOES__</div>

  <div class="cartao largo">
    <h2>Produtos que mais vendem</h2>
    <p class="leitura">Os dez primeiros da seleção, por vendas estimadas (mínimo da faixa). É também a versão em texto dos gráficos.</p>
    <div class="tabela-rolagem"><table><thead><tr>__CABECALHO_TABELA__</tr></thead><tbody id="tabela"></tbody></table></div>
  </div>

  <footer class="rodape">
    <p>Vendas estimadas: o catálogo informa faixas (+100, +1000, +10mil…); aqui vale o limite inferior da faixa. Os totais são, portanto, um mínimo.</p>
    <p>Temas das avaliações: contagem por palavras-chave nas três avaliações de cada produto; mostra o que se comenta, não se é elogio ou crítica.</p>
    <p>Marcas e públicos foram padronizados (ex.: “Stillger Jeans” e “Stillger” viram uma só); anúncios sem marca identificável ficam fora do ranking de marcas. Desconto lido como percentual. Base: ecommerce_estatistica.csv, de exercícios anteriores do curso.</p>
  </footer>
</div>

<script>
const DADOS = __DADOS__;
const CONFIG = __CONFIG__;
const CHAVES = __CHAVES__;
const NUMERICAS = __NUMERICAS__;
const filtro = { publico: "Todos", faixa: "todas", repetidos: "u" };

function el(tag, classe, texto) {
  const e = document.createElement(tag);
  if (classe) e.className = classe;
  if (texto !== undefined) e.textContent = texto;   // textContent: os textos vêm do CSV
  return e;
}

function renderizar() {
  const chave = [filtro.faixa, filtro.publico, filtro.repetidos].join("|");
  const estado = DADOS.estados[chave];
  Object.keys(filtro).forEach(k => {
    document.querySelectorAll("#seg-" + k + " button").forEach(b =>
      b.setAttribute("aria-pressed", String(b.dataset.valor === filtro[k])));
  });

  document.getElementById("kpis").replaceChildren(...estado.kpis.map(k => {
    const d = el("div", "kpi");
    d.append(el("div", "kpi-rotulo", k.rotulo), el("div", "kpi-valor", k.valor), el("div", "kpi-ref", k.ref));
    return d;
  }));

  CHAVES.forEach(c => {
    const fig = DADOS.figuras[estado.figs[c]];
    document.getElementById("leitura-" + c).textContent = estado.leituras[c];
    Plotly.react(c, fig.data, fig.layout, CONFIG);
  });

  document.getElementById("tabela").replaceChildren(...estado.tabela.map(linha => {
    const tr = el("tr");
    linha.forEach((v, i) => tr.append(el("td", NUMERICAS.includes(i) ? "num" : "", v)));
    return tr;
  }));
}

Object.keys(filtro).forEach(k => {
  document.getElementById("seg-" + k).addEventListener("click", e => {
    const b = e.target.closest("button");
    if (b) { filtro[k] = b.dataset.valor; renderizar(); }
  });
});
renderizar();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--offline", action="store_true", help="embute o Plotly no arquivo")
    parser.add_argument("-o", "--saida", default=str(PASTA / "dashboard.html"))
    args = parser.parse_args()
    pagina = montar_pagina(dados.carregar(), args.offline)
    Path(args.saida).write_text(pagina, encoding="utf-8")
    print(f"Gerado: {args.saida} ({len(pagina) / 1e6:.2f} MB)")
