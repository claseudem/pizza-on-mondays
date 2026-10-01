# Pizza on Mondays — documentación de la app

Dashboard en Streamlit para armar fichas de empresas individuales y comparar un activo
contra un benchmark. Todos los precios se descargan en vivo de Yahoo Finance vía
[`yfinance`](https://github.com/ranaroussi/yfinance); no hay datasets estáticos.

App en vivo: https://pizzaonmondays.streamlit.app/

> ⚠️ Todo lo que muestra la app es una lectura descriptiva de datos históricos, no
> asesoramiento financiero.

## Cómo correrla

Requiere Python 3.12+ y [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run streamlit run src/pizza_on_mondays/app.py
```

## Estructura

Es una app **multi-page** de Streamlit con navegación explícita (`st.navigation` +
`st.Page`): `app.py` es un entrypoint delgado que solo declara la lista de páginas y las
ejecuta — no tiene UI propia, así que en el sidebar **solo aparecen las páginas**
("Inicio", "Descriptor de empresas", "QuantStats vs Benchmark"), no un ítem "app".

```
src/pizza_on_mondays/
├── app.py       # entrypoint: declara las páginas y llama st.navigation(...).run()
├── sectors.py   # SECTORS: tickers agrupados por sector, usado por QuantStats
├── ui.py        # helpers de estilo compartidos (títulos/subtítulos coloreados)
└── pages/
    ├── 1_🏠_Inicio.py                    # landing de bienvenida
    ├── 2_🔎_Descriptor_de_empresas.py    # ficha de una empresa a partir de sus fundamentals
    └── 3_📈_QuantStats_vs_Benchmark.py   # tearsheet de un activo vs. un benchmark
```

## Página 1 — Inicio (`pages/1_🏠_Inicio.py`)

Landing de bienvenida: una descripción corta de la app y accesos directos
(`st.page_link`) a las otras dos páginas. No hace llamadas a APIs externas ni cómputo,
así que carga instantáneo.

## Página 2 — Descriptor de empresas (`pages/2_🔎_...py`)

Dado un ticker (`AAPL`, `XOM`, `O`, etc.), arma una descripción en viñetas a partir de
`yf.Ticker(ticker).info`: tamaño (market cap), valoración (P/E trailing y forward),
rentabilidad (margen neto, ROE), crecimiento de ingresos, salud financiera
(deuda/patrimonio, current ratio), dividendos, beta y consenso de analistas. Cada bullet
se omite si el campo no viene en la respuesta de Yahoo Finance (no todos los tickers
traen todos los campos, sobre todo criptos/ETFs).

También muestra 8 métricas clave en tarjetas, la descripción del negocio (expandible) y
un resumen anual de ingresos/utilidad neta/EBITDA/free cash flow, sacado de los estados
financieros de `yfinance`.

Cacheada con `@st.cache_data(ttl=3600)` — los fundamentals no cambian de un minuto a
otro, así que se refrescan cada hora en vez de en cada interacción.

## Página 3 — QuantStats vs Benchmark (`pages/3_📈_...py`)

Compara un activo contra un benchmark **invertible** (un ETF como SPY, QQQ, DIA, IWM o
GLD — no un índice puro como `^GSPC`, que no se puede comprar directamente) y genera el
tearsheet completo de [`quantstats`](https://github.com/ranaroussi/quantstats): retornos,
drawdowns, Sharpe, Sortino y demás métricas estándar, embebido como HTML en la página.

El activo se elige de la lista de todos los tickers agrupados por sector en
`sectors.py` (Oil & Gas, Real Estate, Criptomonedas) o como ticker personalizado; lo
mismo para el benchmark.

`quantstats` solo sabe escribir su reporte a un archivo (`qs.reports.html(output=path)`),
así que la función que lo genera escribe a un archivo temporal, lee el HTML como string,
y lo borra — lo que se cachea (`@st.cache_data`) es el string resultante, no el archivo.

## Rendimiento

El cuello de botella de cada corrida es la descarga de precios, porque depende de la API
de Yahoo Finance. Por eso está cacheada: cambiar un control que no afecta los parámetros
de la descarga es prácticamente instantáneo porque reusa los datos ya traídos. La primera
carga de una combinación nueva de `(ticker, start, end)` tarda lo que tarde `yfinance` en
responder.

## Notebooks

`notebooks/ideas.ipynb` es zona de prototipos y exploración, no código de producción.
