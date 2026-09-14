# Módulo 01 — Fundamentos de Python

Primeiro módulo do curso. Introduz a sintaxe da linguagem e as estruturas básicas de programação.

## Notebooks

### [`01-logica-de-programacao.ipynb`](notebooks/01-logica-de-programacao.ipynb)

Anotações da primeira sequência de aulas, construídas de forma incremental.

- **Saída e variáveis** — `print()`, atribuição, impressão de múltiplos valores na mesma chamada
- **Concatenação e f-strings** — as duas formas de montar um texto com valores variáveis, e por que a f-string é mais legível
- **Tipagem** — `type()`, conversão entre `str`, `int` e `float`
- **Condicionais** — `if`, `elif`, `else` aplicados a um cálculo de nota
- **Estruturas de dados** — lista (mutável), tupla (imutável) e dicionário (pares chave-valor); a diferença fica explícita ao tentar `append()` numa tupla
- **Laços** — `for` com `range()`, `enumerate()`, `break`; `while` e `while/else`

### [`02-operadores-basicos.ipynb`](notebooks/02-operadores-basicos.ipynb)

Referência rápida dos operadores da linguagem.

- **Aritméticos** — `+`, `-`, `*`, `/`, `//` (divisão inteira), `%` (resto), `**` (potenciação)
- **Relacionais** — `<`, `<=`, `>`, `>=`, `==`, `!=`
- **Lógicos** — `and`, `or`, `not`, com a tabela-verdade dos quatro casos de cada um

### [`03-exercicios-fim-de-modulo.ipynb`](notebooks/03-exercicios-fim-de-modulo.ipynb)

Exercícios de fixação do módulo.

1. **Cálculo de média** — lê três notas, calcula a média e informa aprovação ou reprovação
2. **Verificação de senha** — compara a entrada com uma senha esperada; o valor é mantido como `str` justamente para aceitar qualquer caractere, e não só dígitos
3. **Listas e dicionários** — percorre uma lista de feedbacks com `for` e exibe os campos de um dicionário de cliente com f-strings

## Projeto do módulo

A entrega avaliada deste módulo é a calculadora, que ficou em repositório próprio por ser um projeto completo:

➡️ **[calculadora-python-shell](https://github.com/gstvhortencio/calculadora-python-shell)** — calculadora interativa em Python e em Shell Script, com documentação de execução e explicação do código.
