import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from quantstats_report import (
    BENCHMARK_TICKERS,
    all_sector_tickers,
    build_quantstats_report,
    load_price_returns,
)
from ui import colored_title


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


render_quantstats()
