import pandas as pd
import streamlit as st
import yfinance as yf
from pypfopt.expected_returns import capm_return

from sectors import SECTORS

# Proxies del mercado para el CAPM: ETFs líquidos que replican índices amplios.
MARKET_TICKERS = {
    "S&P 500 (SPY)": "SPY",
    "Nasdaq 100 (QQQ)": "QQQ",
    "Dow Jones (DIA)": "DIA",
    "Small Caps (IWM)": "IWM",
}

# Rendimiento anual (en %) de la letra del Tesoro de EE. UU. a 13 semanas: la
# referencia estándar de tasa libre de riesgo para el CAPM.
RISK_FREE_TICKER = "^IRX"

ALL_YEARS = "Todos"

SECTOR_ICONS = {
    "Oil & Gas": "🛢️",
    "Real Estate": "🏢",
    "Criptomonedas": "🪙",
}

EXPECTED_RETURN_COL = "Retorno esperado anual (CAPM)"


def first_year() -> int:
    """Primer año con datos según el inicio más temprano de los sectores."""
    return min(pd.Timestamp(sector["start"]).year for sector in SECTORS.values())


def available_years(today: pd.Timestamp | None = None) -> list[int | str]:
    """Opciones del selector de año: "Todos" y luego del año actual al primero."""
    current_year = (today or pd.Timestamp.today()).year
    return [ALL_YEARS, *range(current_year, first_year() - 1, -1)]


def capm_period(year: int | str, today: pd.Timestamp | None = None) -> tuple[str, str]:
    """Rango de fechas [inicio, fin exclusivo) para el año elegido.

    El fin es exclusivo porque yfinance no incluye la fecha `end`: para 2020 se
    pide hasta 2021-01-01 y así entra el 31 de diciembre.
    """
    if year == ALL_YEARS:
        end = (today or pd.Timestamp.today()).normalize() + pd.Timedelta(days=1)
        return f"{first_year()}-01-01", str(end.date())
    return f"{year}-01-01", f"{year + 1}-01-01"


@st.cache_data
def load_prices_with_market(
    tickers: list[str], market_ticker: str, start: str, end: str
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Descarga precios de los activos, del mercado y la tasa libre de riesgo.

    Todo se alinea a los días hábiles del mercado: así los activos que cotizan
    7 días (cripto) no generan retornos de mercado artificiales en 0 los fines
    de semana. La tasa libre de riesgo se devuelve anual y en decimales.
    """
    data = yf.download(
        [*tickers, market_ticker, RISK_FREE_TICKER], start=start, end=end
    )["Close"]
    data = data.loc[data[market_ticker].notna()].ffill()
    return data[tickers], data[[market_ticker]], data[RISK_FREE_TICKER] / 100


def build_capm_expected_returns(
    prices: pd.DataFrame, market_prices: pd.DataFrame, risk_free: pd.Series
) -> pd.DataFrame:
    """Retorno esperado anual por activo según el CAPM: R_i = R_f + β_i (E(R_m) - R_f).

    Se estima activo por activo, recortando el mercado a las fechas en que cada uno
    cotiza: con una sola llamada, un activo que salió a bolsa más tarde (ej. PECO)
    tendría su covarianza medida en su período pero dividida por la varianza del
    mercado de todo el rango, lo que sesga su beta.

    La tasa libre de riesgo de cada activo es el promedio de ^IRX en esa misma
    ventana: anual, como E(R_m), que capm_return anualiza con frequency=252.
    """
    rows = {}
    for ticker in prices.columns:
        asset = prices[[ticker]].dropna()
        market = market_prices.loc[asset.index]
        risk_free_rate = risk_free.loc[asset.index].mean()
        expected = capm_return(
            asset,
            market_prices=market,
            risk_free_rate=risk_free_rate,
            frequency=252,
        )
        asset_returns = asset[ticker].pct_change().dropna()
        market_returns = market.iloc[:, 0].pct_change().dropna()
        rows[ticker] = {
            "Beta": asset_returns.cov(market_returns) / market_returns.var(),
            EXPECTED_RETURN_COL: expected[ticker],
            "Tasa libre de riesgo": risk_free_rate,
            "Desde": asset.index[0].date(),
        }

    capm = pd.DataFrame.from_dict(rows, orient="index")
    return capm.sort_values(EXPECTED_RETURN_COL, ascending=False)
