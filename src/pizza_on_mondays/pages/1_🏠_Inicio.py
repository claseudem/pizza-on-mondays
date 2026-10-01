import streamlit as st

from ui import colored_title


def home_page() -> None:
    colored_title("MoaInvest")
    st.markdown(
        "Bienvenida/o. Este es un dashboard para explorar activos financieros con "
        "datos en vivo de [Yahoo Finance](https://finance.yahoo.com/), sin datasets "
        "estáticos ni configuración previa. Elegí una de las secciones en la barra "
        "lateral, o desde acá:"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.page_link(
            "pages/2_🔎_Descriptor_de_empresas.py",
            label="**Descriptor de empresas**",
            icon="🔎",
        )
        st.caption(
            "Ingresá un ticker (ej. AAPL, XOM, O) y obtené una ficha con sus "
            "fundamentals: valoración, rentabilidad, deuda, dividendos, beta y "
            "consenso de analistas."
        )
    with col2:
        st.page_link(
            "pages/3_📈_QuantStats_vs_Benchmark.py",
            label="**QuantStats vs Benchmark**",
            icon="📈",
        )
        st.caption(
            "Compará un activo contra un benchmark invertible (SPY, QQQ, DIA, IWM, "
            "GLD, u otro) y generá el tearsheet completo de quantstats."
        )
    with col3:
        st.page_link(
            "pages/4_🎯_CAPM.py",
            label="**Retornos esperados (CAPM)**",
            icon="🎯",
        )
        st.caption(
            "Elegí un sector y un año y obtené la beta y el retorno esperado anual "
            "de cada activo según el CAPM, con la tasa libre de riesgo real del "
            "T-Bill a 13 semanas."
        )

    st.caption(
        "⚠️ Todo lo que muestra esta app es una lectura descriptiva de datos "
        "históricos, no una recomendación de inversión."
    )


home_page()
