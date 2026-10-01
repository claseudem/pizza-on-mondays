# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es esto

**MoaInvest** (antes "Pizza on Mondays"): dashboard en Streamlit para explorar el comportamiento histórico de
distintos sectores de mercado (Oil & Gas, Real Estate, Criptomonedas), armar fichas de
empresas individuales a partir de fundamentals, y comparar un activo contra un benchmark
con tearsheets de QuantStats. Datos en vivo vía `yfinance`, sin datasets estáticos.
App en vivo: https://pizzaonmondays.streamlit.app/

## Comandos

Requiere Python 3.12+ y [uv](https://docs.astral.sh/uv/).

```bash
uv sync                                          # instalar/actualizar dependencias
uv run streamlit run src/pizza_on_mondays/app.py # levantar la app localmente
uv run pytest                                    # correr toda la suite de tests
uv run pytest tests/test_descriptor.py           # correr un solo archivo de tests
uv run pytest -k test_fmt_money                  # correr por nombre (substring match)
```

No hay linter ni CI configurados en el repo.

## Arquitectura

Streamlit multi-page app con navegación explícita (`st.navigation` + `st.Page`, API
moderna de Streamlit ≥1.36). El entrypoint `src/pizza_on_mondays/app.py` **no tiene
lógica de negocio ni UI propia**: solo define `PAGES` y llama a
`st.navigation(PAGES).run()`. Por eso en el sidebar solo aparecen las páginas (Inicio,
Descriptor de empresas, QuantStats vs Benchmark) con sus títulos explícitos — no hay una
entrada separada "app" ni depende del nombre de archivo para el label, a diferencia del
mecanismo clásico de detección automática de `pages/`.

Las páginas reales viven en `src/pizza_on_mondays/pages/`, numeradas por prefijo para que
coincidan con el orden declarado en `PAGES` (el número es solo organizativo; el orden y
el título que se ven los define `app.py`, no el nombre de archivo). Ninguna página llama
`st.set_page_config` — se configura una sola vez en `app.py`, antes de
`st.navigation(...)`; si se agrega una página nueva, no repetir esa llamada ahí.

**Import path, no paquete real**: aunque el código vive bajo `src/pizza_on_mondays/`, los
módulos se importan entre sí de forma plana (`from ui import colored_title`,
`from sectors import SECTORS`), no como `pizza_on_mondays.ui`. Esto funciona porque
Streamlit agrega el directorio del script de entrada (`src/pizza_on_mondays/`) al
`sys.path`, y las páginas en `pages/` heredan ese mismo path. Si se agrega un módulo
compartido nuevo, seguir este mismo patrón de import plano en vez de
`from pizza_on_mondays import ...`.

**`ui.py`**: helpers de estilo compartidos entre todas las páginas (títulos/subtítulos
coloreados vía HTML embebido). Cualquier estilo común nuevo va acá, no repetido por página.

**`sectors.py`**: solo el diccionario `SECTORS` (tickers por sector), con nombre de
módulo válido para poder importarse desde una página (`pages/2_🔎_...py`,
`pages/3_📈_...py` no se pueden importar como módulo por el emoji/número en el nombre).
La página de QuantStats lo reimporta (`from sectors import SECTORS`) para poblar el
selector de "activo a analizar" con todos los tickers conocidos por la app — mantenerlo
como la única fuente de esa lista. No hay ya una página de "Sectores" con resumen/
métricas por sector; se eliminó por no aportar valor.

**`pages/1_🏠_Inicio.py`**: landing de bienvenida — una descripción corta de la app y
links (`st.page_link`) a las otras dos páginas. Sin llamadas a APIs externas ni cómputo,
para que cargue instantáneo.

**`descriptor.py`** (consumido por `pages/2_🔎_Descriptor_de_empresas.py`): dado un
ticker, arma una descripción en texto (tamaño, valoración, rentabilidad, deuda,
dividendos, beta, consenso de analistas) leyendo campos sueltos de
`yf.Ticker(ticker).info` — la mayoría de los campos son opcionales y se omiten en el
texto si no vienen en la respuesta de Yahoo Finance (ver los `if` guard antes de cada
bullet en `build_company_description`). Al agregar un campo nuevo, seguir ese mismo
patrón defensivo en vez de asumir que `info` trae todo.

**`quantstats_report.py`** (consumido por `pages/3_📈_QuantStats_vs_Benchmark.py`):
genera un tearsheet HTML completo de `quantstats` (retornos, drawdowns, Sharpe, Sortino,
etc.) comparando un activo contra un benchmark invertible (ETF, no un índice puro como
`^GSPC`). El reporte se escribe a un archivo temporal (`qs.reports.html(...,
output=path)`), se lee como string y se destruye el archivo en un `finally` —
`quantstats` solo sabe escribir a disco, no devolver el HTML directamente. El resultado
cacheado (`@st.cache_data`) es el string, no el archivo.

**Por qué `descriptor.py` y `quantstats_report.py` existen separados de sus páginas**:
igual que `sectors.py`, es para poder testear la lógica pura (formateo, armado de texto,
cálculo de retornos) con pytest importando el módulo directamente, sin pasar por un
archivo de `pages/` que no es importable por el emoji/número en el nombre y sin levantar
Streamlit. Las funciones que sí llaman a la red (`load_fundamentals`, `load_price_returns`)
se testean mockeando `yfinance`, no pegándole a la API real.

## Tests

`tests/` espeja los módulos de `src/pizza_on_mondays/` (`test_sectors.py`, `test_ui.py`,
`test_descriptor.py`, `test_quantstats_report.py`). `pyproject.toml` agrega
`src/pizza_on_mondays` a `pythonpath` para que los tests puedan hacer los mismos imports
planos que el código de la app (`from sectors import SECTORS`, no
`from pizza_on_mondays.sectors import SECTORS`). Las llamadas a `yfinance` se mockean con
`pytest-mock` (fixture `mocker`) en vez de pegarle a la red real.

## Notebooks

`notebooks/ideas.ipynb` es zona de prototipos/exploración, no código de producción de la
app.
