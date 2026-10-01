import os
import tempfile

import pandas as pd
import quantstats as qs
import streamlit as st
import yfinance as yf

from sectors import SECTORS

# ETFs líquidos: se pueden comprar directamente, a diferencia de un índice puro (ej. ^GSPC).
BENCHMARK_TICKERS = {
    "S&P 500 (SPY)": "SPY",
    "Nasdaq 100 (QQQ)": "QQQ",
    "Dow Jones (DIA)": "DIA",
    "Small Caps (IWM)": "IWM",
    "Oro (GLD)": "GLD",
}


def all_sector_tickers() -> list[str]:
    return sorted({ticker for sector in SECTORS.values() for ticker in sector["stocks"]})


@st.cache_data
def load_price_returns(ticker: str, start: str, end: str) -> pd.Series:
    data = yf.download(ticker, start=start, end=end)["Close"]
    if isinstance(data, pd.DataFrame):
        data = data.iloc[:, 0]
    data = data.ffill().bfill()
    return data.pct_change().dropna().rename(ticker)


@st.cache_data(show_spinner=False)
def build_quantstats_report(
    returns: pd.Series, benchmark: pd.Series, asset: str, benchmark_ticker: str
) -> str:
    """Genera el tearsheet HTML de quantstats (gráficos embebidos como SVG)."""
    fd, output_path = tempfile.mkstemp(suffix=".html")
    os.close(fd)
    try:
        qs.reports.html(
            returns,
            benchmark=benchmark,
            output=output_path,
            title=f"{asset} vs {benchmark_ticker}",
            download_filename=f"quantstats_{asset}_vs_{benchmark_ticker}.html",
        )
        with open(output_path, encoding="utf-8") as f:
            return f.read()
    finally:
        os.remove(output_path)
