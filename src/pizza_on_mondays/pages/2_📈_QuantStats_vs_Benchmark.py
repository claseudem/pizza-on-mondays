import os
import tempfile

import pandas as pd
import quantstats as qs
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf

from app import SECTORS
from ui import colored_title

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


def render_quantstats() -> None:
    colored_title("📈 QuantStats: Activo vs Benchmark")
    st.caption(
        "Elegí un activo y un benchmark invertible (un ETF que efectivamente puedas "
        "comprar, no un índice puro como el ^GSPC) para generar el tearsheet completo "
        "de quantstats: retornos, drawdowns, Sharpe, Sortino y demás métricas estándar."
    )

    col1, col2 = st.columns(2)
    asset_label = col1.selectbox(
        "Activo a analizar",
        [*all_sector_tickers(), "Personalizado"],
        key="qs_asset_label",
    )
    if asset_label == "Personalizado":
        asset = col1.text_input(
            "Ticker del activo", value="AAPL", key="qs_asset_custom"
        ).strip().upper()
    else:
        asset = asset_label

    benchmark_label = col2.selectbox(
        "Benchmark",
        [*BENCHMARK_TICKERS.keys(), "Personalizado"],
        key="qs_benchmark_label",
    )
    if benchmark_label == "Personalizado":
        benchmark_ticker = col2.text_input(
            "Ticker del benchmark", value="SPY", key="qs_benchmark_custom"
        ).strip().upper()
    else:
        benchmark_ticker = BENCHMARK_TICKERS[benchmark_label]

    col3, col4 = st.columns(2)
    start = col3.date_input("Desde", value=pd.Timestamp("2020-01-01"), key="qs_start")
    end = col4.date_input("Hasta", value=pd.Timestamp.today(), key="qs_end")

    if not asset:
        st.info("Ingresá un ticker de activo.")
        return
    if not benchmark_ticker:
        st.info("Ingresá un ticker de benchmark.")
        return
    if asset == benchmark_ticker:
        st.warning("Elegí un activo distinto al benchmark para poder compararlos.")
        return

    if st.button("Generar análisis", key="qs_generate"):
        with st.spinner("Descargando datos y generando el tearsheet de quantstats..."):
            asset_returns = load_price_returns(asset, str(start), str(end))
            benchmark_returns = load_price_returns(benchmark_ticker, str(start), str(end))

            if asset_returns.empty or benchmark_returns.empty:
                st.error("No se encontraron datos para el período y tickers seleccionados.")
                return

            html_report = build_quantstats_report(
                asset_returns, benchmark_returns, asset, benchmark_ticker
            )
        components.html(html_report, height=1600, scrolling=True)


def main() -> None:
    st.set_page_config(
        page_title="QuantStats: Activo vs Benchmark", page_icon="📈", layout="wide"
    )
    render_quantstats()


if __name__ == "__main__":
    main()
