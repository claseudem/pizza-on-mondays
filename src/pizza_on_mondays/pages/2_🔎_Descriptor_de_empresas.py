import streamlit as st

from descriptor import build_company_description, fmt_money, fmt_num, load_fundamentals
from ui import colored_title


def render_company_descriptor() -> None:
    colored_title("🔎 Descriptor de empresas")
    ticker = st.text_input(
        "Ticker de la acción (ej. AAPL, XOM, O)", key="descriptor_ticker"
    ).strip().upper()
    if not ticker:
        return

    with st.spinner(f"Buscando fundamentals de {ticker}..."):
        info, financials = load_fundamentals(ticker)

    if not (info.get("longName") or info.get("shortName")):
        st.warning(f"No se encontró información para **{ticker}**. Revisá el ticker.")
        return

    if info.get("quoteType") not in (None, "EQUITY"):
        st.info(
            f"{ticker} es de tipo {info.get('quoteType')}: no tiene fundamentals de empresa, "
            "solo se muestra el perfil básico."
        )

    st.markdown(build_company_description(info))

    currency = info.get("currency", "USD")
    cols = st.columns(4)
    cols[0].metric("Market cap", fmt_money(info.get("marketCap"), currency))
    cols[1].metric("P/E (trailing)", fmt_num(info.get("trailingPE"), "{:.1f}x"))
    cols[2].metric("P/B", fmt_num(info.get("priceToBook"), "{:.2f}x"))
    cols[3].metric("EV/EBITDA", fmt_num(info.get("enterpriseToEbitda"), "{:.1f}x"))
    cols = st.columns(4)
    cols[0].metric("Margen neto", fmt_num(info.get("profitMargins"), "{:.1%}"))
    cols[1].metric("ROE", fmt_num(info.get("returnOnEquity"), "{:.1%}"))
    cols[2].metric("Dividend yield", fmt_num(info.get("dividendYield"), "{:.2f}%"))
    cols[3].metric("Beta", fmt_num(info.get("beta")))

    if info.get("longBusinessSummary"):
        with st.expander("Descripción del negocio (Yahoo Finance)"):
            st.write(info["longBusinessSummary"])
            if info.get("website"):
                st.markdown(f"🌐 {info['website']}")

    if not financials.empty:
        st.markdown(f"**Estados financieros anuales ({currency})**")
        st.bar_chart(financials[[c for c in ("Ingresos", "Utilidad neta") if c in financials]])
        st.dataframe(financials.T.style.format(lambda v: fmt_money(v, "")))


render_company_descriptor()
