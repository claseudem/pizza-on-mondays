<p align="center">
  <a href="https://pizzaonmondays.streamlit.app/"><img src="https://static.streamlit.io/badges/streamlit_badge_black_white.svg" alt="Open in Streamlit"></a>
</p>
<p align="center">
  <em>🍕 MoaInvest — dashboard de retornos, riesgo y simulación de cartera por sector</em>
</p>
<p align="center">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/streamlit-1.63%2B-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit">
</p>

---

**App en vivo**: [https://pizzaonmondays.streamlit.app/](https://pizzaonmondays.streamlit.app/)

**Código fuente**: [https://github.com/claseudem/pizza-on-mondays](https://github.com/claseudem/pizza-on-mondays)

---

**MoaInvest** es un dashboard interactivo en Streamlit para explorar el comportamiento histórico de distintos sectores (Oil & Gas, Real Estate, Criptomonedas) y simular una cartera simple sobre ellos, sin salir del navegador.

Lo principal:

- **Multi-sector**: cambiá entre Oil & Gas 🛢️, Real Estate 🏢 y Criptomonedas desde un mismo selector.
- **Resumen accionable**: retorno total/anualizado, volatilidad, Sharpe aproximado, máximo drawdown y momentum, ordenados de mejor a peor.
- **Recomendación automática**: una lectura en texto plano de esas métricas, generada en cada corrida.
- **Simulación de payoff**: proyectá un capital inicial sobre cada activo y sobre una cartera equiponderada.
- **Datos en vivo**: precios descargados de Yahoo Finance vía [yfinance](https://github.com/ranaroussi/yfinance), sin datasets estáticos.
- **Descriptor de empresas** 🔎 (página aparte): ingresando un ticker, arma una descripción de la empresa a partir de sus fundamentals (perfil, valoración, rentabilidad, deuda, dividendos y estados financieros).

> ⚠️ Todo lo que muestra la app es una lectura descriptiva de datos históricos, no asesoramiento financiero.

## Código y resultado en la app

Recorrido por cada bloque de [`app.py`](src/pizza_on_mondays/app.py) y qué produce en https://pizzaonmondays.streamlit.app/

### 1. Selección de sector y rango de fechas

```python
sector_name = st.selectbox(
    "Sector",
    list(SECTORS.keys()),
    format_func=lambda name: f"{SECTOR_ICONS.get(name, '')} {name}",
)
sector = SECTORS[sector_name]

start = col1.date_input("Desde", value=pd.Timestamp(sector["start"]), key=f"start_{sector_name}")
end = col2.date_input("Hasta", value=pd.Timestamp(sector["end"]), key=f"end_{sector_name}")
```

**En la app:** un desplegable para elegir entre *Oil & Gas* 🛢️, *Real Estate* 🏢 o *Criptomonedas*, y dos selectores de fecha lado a lado para acotar el período de análisis.

### 2. Descarga y limpieza de retornos

```python
@st.cache_data
def load_returns(tickers, start, end):
    data = yf.download(tickers, start=start, end=end)["Close"]
    data = data.ffill().bfill()
    return data.pct_change().dropna()
```

**En la app:** no se ve directamente — es el paso que trae los precios desde Yahoo Finance y calcula los retornos diarios que alimentan todo lo demás. Está cacheado (`@st.cache_data`) para no re-descargar en cada interacción.

### 3. Resumen y recomendación

```python
summary = build_summary(returns)
st.dataframe(summary.style.format({...}))
st.markdown(build_recommendation(summary))
```

**En la app:** una tabla con, por cada ticker, retorno total, retorno anualizado, volatilidad anualizada, Sharpe aproximado, máximo drawdown y momentum reciente — ordenada de mejor a peor Sharpe. Justo debajo, una lista en texto (viñetas) que destaca el mejor Sharpe, el mejor y peor momentum, el activo más volátil y el peor drawdown del período.

### 4. Retornos diarios y estadísticas

```python
st.dataframe(returns)
st.dataframe(returns.describe())
```

**En la app:** una tabla con los retornos diarios crudos de cada ticker, seguida de las estadísticas descriptivas estándar de pandas (media, desvío, mínimo, máximo, cuartiles).

### 5. Retornos acumulados

```python
st.line_chart((1 + returns).cumprod())
```

**En la app:** un gráfico de líneas con la evolución acumulada de cada activo a lo largo del período (base 1 = capital inicial normalizado).

### 6. Simulación de payoff

```python
initial_capital = st.number_input("Capital inicial", min_value=1.0, value=10_000.0, step=500.0)
payoff, portfolio_returns = simulate_payoff(returns, initial_capital)
st.line_chart(payoff)
st.dataframe(payoff_metrics(portfolio_returns).to_frame("Cartera").style.format("{:.2%}"))
```

**En la app:** un campo para ingresar el capital inicial, un gráfico de líneas mostrando cómo hubiera evolucionado ese capital en cada activo y en una cartera equiponderada ("Cartera"), y una tabla con retorno anualizado, Sharpe y máximo drawdown de esa cartera (vía QuantStats).

### 7. Volatilidad rolling

```python
st.line_chart(returns.rolling(21).std() * (252 ** 0.5))
```

**En la app:** un gráfico de líneas con la volatilidad anualizada calculada en ventanas móviles de 21 días hábiles (~1 mes), por activo.

### 8. Dispersión entre activos

```python
tickers = st.multiselect("Tickers a comparar", options=list(returns.columns), default=list(returns.columns[:4]))
if len(tickers) >= 2:
    fig = sns.pairplot(returns[tickers], kind="scatter", plot_kws={"alpha": 0.5})
    st.pyplot(fig.figure)
```

**En la app:** un selector múltiple de tickers y, al elegir dos o más, una matriz de gráficos de dispersión (pairplot de seaborn) mostrando cómo se relacionan los retornos diarios entre esos activos.

### 9. Descriptor de empresas (página aparte)

Vive en [`pages/1_🔎_Descriptor_de_empresas.py`](src/pizza_on_mondays/pages/1_🔎_Descriptor_de_empresas.py); Streamlit la detecta sola por estar en la carpeta `pages/`.

```python
ticker = st.text_input("Ticker de la acción (ej. AAPL, XOM, O)").strip().upper()
info, financials = load_fundamentals(ticker)  # yf.Ticker(ticker).info + estados financieros
st.markdown(build_company_description(info))
```

**En la app:** en la barra lateral aparece *🔎 Descriptor de empresas*. Al ingresar un ticker muestra una descripción en viñetas (tamaño, valoración, rentabilidad, salud financiera, dividendos, beta y consenso de analistas), 8 métricas clave, la descripción del negocio y los estados financieros anuales. Si el ticker no existe, muestra un aviso; para criptos/ETFs, solo el perfil básico.

## Rendimiento

La descarga de precios (`load_returns`) es lo más costoso de cada corrida, porque depende de la API de Yahoo Finance. Por eso está detrás de `@st.cache_data`: Streamlit cachea el resultado por combinación de `(tickers, start, end)`, así que cambiar un selector que no afecta esos parámetros (por ejemplo, el capital inicial o los tickers a comparar en la dispersión) **no vuelve a descargar nada** — solo recalcula sobre los datos ya cacheados.

En la práctica esto significa que la primera carga de un sector/rango de fechas tarda lo que tarde yfinance en responder, pero cualquier interacción posterior dentro de ese mismo sector y rango es prácticamente instantánea.

## Cómo correrlo localmente

Requiere Python 3.12+ y [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run streamlit run src/pizza_on_mondays/app.py
```

## Estructura del proyecto

```
src/pizza_on_mondays/
├── __init__.py
├── app.py          # entrypoint de Streamlit: página de Sectores
├── ui.py           # helpers de estilo compartidos entre páginas
└── pages/
    └── 1_🔎_Descriptor_de_empresas.py   # ficha de una empresa con fundamentals de yfinance
notebooks/
└── ideas.ipynb      # exploración y prototipos
```
