# Módulo 02 — Visualização de Dados

Segundo módulo do curso. Aplica `matplotlib` e `seaborn` sobre uma base de e-commerce para praticar a escolha do gráfico certo para cada pergunta, e depois leva a mesma análise para um dashboard interativo em Dash e Plotly.

## Notebook

### [`01-visualizacao-ecommerce.ipynb`](notebooks/01-visualizacao-ecommerce.ipynb)

Exploração de um catálogo de produtos de moda, com uma leitura escrita para cada gráfico — não só o código, a conclusão que ele sustenta.

| Gráfico | Pergunta |
|---|---|
| Histograma | Como os preços do catálogo se distribuem? |
| Dispersão | Preço mais alto puxa nota melhor? |
| Mapa de calor | Quais variáveis numéricas se relacionam entre si? |
| Barras | Quais marcas concentram o volume de vendas? |
| Pizza | Como o catálogo se divide por público? |
| Densidade (KDE) | A distribuição de preço muda entre masculino e feminino? |
| Regressão | Número de avaliações antecipa quantidade vendida? |

**Principais leituras:**

- Preço e nota não se relacionam (correlação ≈ 0) — cobrar mais não penaliza nem melhora a avaliação
- Número de avaliações e quantidade vendida têm correlação de 0,91 — na ausência do dado exato de vendas, avaliações funcionam como proxy razoável
- Vendas são concentradas: a marca líder responde por ~30% do volume estimado
- Mediana de preço é bem mais alta no público masculino (≈ R$ 153) do que no feminino (≈ R$ 80)

**Dados:** `ecommerce_estatistica.csv`, base já usada em exercícios anteriores do curso — as colunas com sufixo `_Cod`, `_Freq` e `_MinMax` vêm dessas etapas prévias de codificação e normalização, mantidas aqui como entraram no módulo.

## Dashboard

### [`dashboard/`](dashboard/)

A mesma base em versão interativa: cinco indicadores, oito gráficos em Plotly e uma tabela, com filtros por público, faixa de preço e anúncios repetidos. Roda como app Dash e também exporta um HTML único. Detalhes, como rodar e limites estão no [README do dashboard](dashboard/README.md).

![Visão geral do dashboard: filtros, cinco indicadores e gráficos de preço, marcas e público](dashboard/imagens/visao-geral.png)

## Como abrir o notebook

O notebook já roda com os gráficos salvos — abrem direto aqui no GitHub, sem precisar executar nada. Para rodar:

```bash
pip install pandas numpy matplotlib seaborn notebook
jupyter notebook
```

Abra a partir de `notebooks/`, com a pasta `data/` um nível acima — é o caminho que o notebook espera.
