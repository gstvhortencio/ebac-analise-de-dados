"""Leitura, limpeza, indicadores e formatação da base ecommerce_estatistica.csv."""
import re
import unicodedata
from pathlib import Path
from string import capwords

import pandas as pd

CSV = Path(__file__).resolve().parent.parent / "data" / "ecommerce_estatistica.csv"

TODOS = "Todos"
PUBLICOS = ["Masculino", "Feminino", "Infantil", "Sem gênero / Unissex"]
SEM_MARCA = "Sem marca definida"
# Mesmo título + preço + marca = o mesmo anúncio coletado mais de uma vez.
CHAVE_ANUNCIO = ["Título", "Preço", "Marca"]


# ---------------------------------------------------------------- público (gênero)

def _sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()


def definir_publico(genero: str, titulo: str) -> str:
    """Agrupa as categorias de gênero em quatro públicos.

    Quando o cadastro não diz o gênero (ou traz um texto solto, como "roupa para gordinha"),
    o título do anúncio decide, mas só se ele for inequívoco.
    """
    if genero in ("Masculino", "Feminino"):
        return genero
    if genero in ("Meninos", "Meninas", "Sem gênero infantil", "Bebês"):
        return "Infantil"
    t = _sem_acento(titulo)
    if re.search(r"\b(infantil|crianca|menino|menina|bebe)\b", t):
        return "Infantil"
    masculino = re.search(r"\b(masculin\w*|homem)\b", t)
    feminino = re.search(r"\b(feminin\w*|mulher)\b", t)
    if masculino and not feminino:
        return "Masculino"
    if feminino and not masculino:
        return "Feminino"
    return "Sem gênero / Unissex"


# ---------------------------------------------------------------- marca

# Variações do mesmo nome (chave em minúsculas, como vem no CSV) -> nome único.
MARCA_EQUIVALENTE = {
    "stillger jeans": "Stillger", "sawary jeans": "Sawary", "daze modas": "Daze",
    "neve segunda pele térmica": "Neve", "calvin klein underwear": "Calvin Klein", "malwee kids": "Malwee",
}
PREFIXOS_EQUIVALENTES = {"mallbeck": "Mallbeck"}   # o cadastro cola a descrição do produto depois do nome

# Campos que não são marca: "própria", "genérica", "não definido" ou uma descrição de produto.
NAO_E_MARCA = {
    "própria", "propria", "fabricacao propria", "confecção própria", "genérica", "nacional", "produto nacional",
    "não definido", "multimarcas", "tactel slim calça ziper", "steelflex epi tipo 6 roupa descartável",
    "camiseta uv masculina camisa", "short menina mulher look verão", "camiseta térmica/mundo térmico",
    "kit frio inverno, blusa manga longa segunda pele,", "kit bermuda feminina academia ginástica atacado",
    "feminina academia atacado", "beleza feminina", "bailarina profissional", "time fitness roupa de dormir",
}
SIGLAS = {"gtz": "GTZ", "spk": "SPK", "sm": "SM", "ak art lover": "AK Art Lover", "ak fashion kids": "AK Fashion Kids",
          "kn3kids": "KN3Kids", "ems textil": "EMS Textil", "amx acessorios": "AMX Acessorios", "mr fit": "MR Fit"}


def padronizar_marca(marca: str) -> str:
    m = " ".join(marca.lower().split())
    if m in MARCA_EQUIVALENTE:
        return MARCA_EQUIVALENTE[m]
    for prefixo, nome in PREFIXOS_EQUIVALENTES.items():
        if m.startswith(prefixo):
            return nome
    if m in NAO_E_MARCA or len(m) > 40:
        return SEM_MARCA
    return SIGLAS.get(m, capwords(m))


# ---------------------------------------------------------------- temas das avaliações

# Classificação por palavras-chave (sem acento), não por modelo de linguagem.
TEMAS = {
    "Tamanho e caimento": r"\b(?:tamanho\w*|numeracao|apertad\w*|folgad\w*|largo|larga|justo|justa|pequen\w*|"
                          r"caimento|modelagem|medidas?|serviu|vestiu|veste)\b",
    "Tecido e material": r"\b(?:tecido\w*|material|malha|algodao|elastano|poliamida|poliester|microfibra|pano|"
                         r"grosso|grossa|fino|fina|transparente|lycra)\b",
    "Qualidade e durabilidade": r"\b(?:qualidade|duravel|durabilidade|resistente|bolinhas?|desbot\w*|encolh\w*|"
                                r"rasg\w*|furou|furad\w*|costuras?|acabamento|lavagens?|estragou|defeito\w*|durou)\b",
    "Conforto": r"\b(?:confortavel|confortaveis|conforto|macio\w*|macia|quentinh\w*|gostos\w*|leve|aconchegante)\b",
    "Preço e custo-benefício": r"\b(?:preco\w*|custo[- ]beneficio|barat\w*|valor|vale a pena|caro|cara)\b",
    "Entrega e anúncio": r"\b(?:entrega\w*|chegou|chegaram|prazo|embalagem|veio|vieram|foto|anuncio\w*|anunciad\w*|"
                         r"original|replica|falsa|falso|descricao|cores?|vendedor\w*)\b",
}
COLUNAS_REVIEW = ["Review1", "Review2", "Review3"]


def _contar_temas(df: pd.DataFrame) -> pd.DataFrame:
    """Para cada produto e tema: em quantas das 3 avaliações (0 a 3) o tema aparece."""
    texto = df[COLUNAS_REVIEW].apply(lambda col: col.fillna("").map(_sem_acento))
    return pd.DataFrame({
        f"Tema: {tema}": sum(texto[c].str.contains(padrao, regex=True).astype(int) for c in COLUNAS_REVIEW)
        for tema, padrao in TEMAS.items()
    }, index=df.index)


# ---------------------------------------------------------------- carga e filtros

def carregar() -> pd.DataFrame:
    df = pd.read_csv(CSV).drop(columns=["Unnamed: 0"], errors="ignore")
    df["Público"] = [definir_publico(g, t) for g, t in zip(df["Gênero"], df["Título"])]
    df["Marca"] = df["Marca"].map(padronizar_marca)
    df = df.join(_contar_temas(df))
    # Marca como "repetida" as cópias de um anúncio, mantendo a linha com mais avaliações.
    ordenado = df.sort_values("N_Avaliações", ascending=False)
    df["Repetido"] = ordenado.duplicated(CHAVE_ANUNCIO).reindex(df.index)
    return df


def filtrar(df: pd.DataFrame, publico: str = TODOS, preco: tuple | None = None,
            unicos: bool = False) -> pd.DataFrame:
    if unicos:
        df = df[~df["Repetido"]]
    if publico != TODOS:
        df = df[df["Público"] == publico]
    if preco:
        df = df[df["Preço"].between(preco[0], preco[1])]
    return df


# ---------------------------------------------------------------- formatação pt-BR

def _br(texto: str) -> str:
    """Troca separadores do formato americano (1,234.50) para o brasileiro (1.234,50)."""
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def inteiro(n: float) -> str:
    return _br(f"{n:,.0f}")


def decimal(x: float, casas: int = 2) -> str:
    return _br(f"{x:,.{casas}f}")


def reais(x: float, casas: int = 2) -> str:
    return "R$ " + decimal(x, casas)


def compacto(n: float) -> str:
    if n >= 1_000_000:
        return decimal(n / 1_000_000, 1) + " mi"
    if n >= 10_000:
        return decimal(n / 1_000, 0) + " mil"
    if n >= 1_000:
        return decimal(n / 1_000, 1) + " mil"
    return inteiro(n)


def reais_compacto(n: float) -> str:
    return "R$ " + compacto(n)


# ---------------------------------------------------------------- indicadores

ROTULOS_KPI = ["Produtos", "Preço médio", "Desconto médio", "Nota média",
               "Vendas estimadas (mín.)"]


def _indicadores(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["—"] * len(ROTULOS_KPI)
    return [
        inteiro(len(df)),
        reais(df["Preço"].mean()),
        decimal(df["Desconto"].mean(), 0) + "%",
        decimal(df["Nota"].mean()),
        compacto(df["Qtd_Vendidos_Cod"].sum()),
    ]


def kpis(df: pd.DataFrame, total: pd.DataFrame) -> list[dict]:
    """Indicadores da seleção; quando há filtro, mostra o valor do catálogo como referência."""
    filtrado = len(df) != len(total)
    return [
        {"rotulo": rot, "valor": val, "ref": f"Catálogo: {ref}" if filtrado else ""}
        for rot, val, ref in zip(ROTULOS_KPI, _indicadores(df), _indicadores(total))
    ]


def nota_repetidos(total: pd.DataFrame) -> str:
    repetidos = int(total["Repetido"].sum())
    return (f"{repetidos} das {len(total)} linhas repetem um anúncio já listado (mesmo título, preço e marca) "
            f"e distorcem totais e participações. “Remover” deixa {len(total) - repetidos} produtos; "
            "“Manter” reproduz a base completa do notebook.")
