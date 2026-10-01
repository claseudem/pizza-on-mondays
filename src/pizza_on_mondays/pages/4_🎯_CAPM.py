import streamlit as st

from capm import (
    EXPECTED_RETURN_COL,
    MARKET_TICKERS,
    RISK_FREE_TICKER,
    SECTOR_ICONS,
    available_years,
    build_capm_expected_returns,
    capm_period,
    load_prices_with_market,
)
from sectors import SECTORS
from ui import colored_title


def render_capm() -> None:
    colored_title("🎯 Retornos esperados (CAPM)")
    st.caption(
        "Retorno esperado anual de cada activo según el CAPM, "
        "R_i = R_f + β_i (E(R_m) − R_f), calculado con PyPortfolioOpt. Elegí un "
        "sector, un año y el ETF que hace de proxy del mercado."
    )

    sector_name = st.segmented_control(
        "Sector",
        list(SECTORS.keys()),
        default=list(SECTORS.keys())[0],
        required=True,
        format_func=lambda name: f"{SECTOR_ICONS.get(name, '')} {name}",
        key="capm_sector",
    )
    year = st.segmented_control(
        "Año", available_years(), default=available_years()[0], required=True, key="capm_year"
    )
    market_label = st.selectbox(
        "Proxy del mercado", list(MARKET_TICKERS.keys()), key="capm_market"
    )

    start, end = capm_period(year)
    with st.spinner("Descargando precios y tasa libre de riesgo..."):
        prices, market_prices, risk_free = load_prices_with_market(
            SECTORS[sector_name]["stocks"], MARKET_TICKERS[market_label], start, end
        )

    if prices.empty:
        st.error("No se encontraron datos para el sector y año seleccionados.")
        return
    if risk_free.isna().all():
        st.warning(
            f"No se pudo descargar la tasa libre de riesgo ({RISK_FREE_TICKER}) "
            "desde Yahoo Finance; probá de nuevo en unos minutos."
        )
        return

    capm = build_capm_expected_returns(prices, market_prices, risk_free)
    st.metric(
        "Tasa libre de riesgo al cierre del período (T-Bill 13 semanas, ^IRX)",
        f"{risk_free.dropna().iloc[-1]:.2%}",
    )
    st.dataframe(
        capm.style.format(
            {
                "Beta": "{:.2f}",
                EXPECTED_RETURN_COL: "{:.1%}",
                "Tasa libre de riesgo": "{:.2%}",
            }
        )
    )
    st.caption(
        "Cada activo se estima sobre su propio período (columna *Desde*), alineado a "
        "los días hábiles del mercado. La tasa libre de riesgo es el promedio del "
        "rendimiento de la letra del Tesoro de EE. UU. a 13 semanas (^IRX, Yahoo "
        "Finance) en ese mismo período, anual como E(R_m)."
    )
    st.caption(
        "⚠️ Es una lectura descriptiva de datos históricos, no una recomendación de "
        "inversión."
    )


render_capm()
