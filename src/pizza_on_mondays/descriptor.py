import pandas as pd
import streamlit as st
import yfinance as yf


@st.cache_data(ttl=3600)
def load_fundamentals(ticker: str) -> tuple[dict, pd.DataFrame]:
    """Trae el perfil (`info`) y un resumen anual de estados financieros de yfinance."""
    t = yf.Ticker(ticker)
    try:
        info = t.info or {}
    except Exception:
        info = {}

    rows = {
        "Ingresos": (t.income_stmt, "Total Revenue"),
        "Utilidad neta": (t.income_stmt, "Net Income"),
        "EBITDA": (t.income_stmt, "EBITDA"),
        "Free cash flow": (t.cashflow, "Free Cash Flow"),
    }
    financials = {}
    for label, (statement, row) in rows.items():
        if statement is not None and row in statement.index:
            financials[label] = statement.loc[row]
    financials = pd.DataFrame(financials)
    if not financials.empty:
        financials.index = pd.to_datetime(financials.index).year
        financials = financials.sort_index().dropna(how="all")
    return info, financials


def fmt_money(value, currency: str = "USD") -> str:
    if value is None or pd.isna(value):
        return "N/D"
    for size, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
        if abs(value) >= size:
            return f"{value / size:,.2f} {suffix} {currency}"
    return f"{value:,.0f} {currency}"


def fmt_num(value, pattern: str = "{:.2f}") -> str:
    return "N/D" if value is None or pd.isna(value) else pattern.format(value)


def build_company_description(info: dict) -> str:
    """Arma una descripción en texto a partir de los fundamentals de yfinance."""
    name = info.get("longName") or info.get("shortName") or info.get("symbol")
    currency = info.get("currency", "USD")

    location = ", ".join(p for p in (info.get("city"), info.get("country")) if p)
    intro = f"**{name}** ({info.get('symbol')})"
    if info.get("sector"):
        intro += f" opera en el sector **{info['sector']}**"
        if info.get("industry"):
            intro += f", industria **{info['industry']}**"
    if location:
        intro += f", con sede en {location}"
    if info.get("fullTimeEmployees"):
        intro += f" y cerca de {info['fullTimeEmployees']:,} empleados"
    lines = [intro + "."]

    market_cap = info.get("marketCap")
    if market_cap:
        size = (
            "mega cap" if market_cap >= 200e9
            else "large cap" if market_cap >= 10e9
            else "mid cap" if market_cap >= 2e9
            else "small cap"
        )
        lines.append(
            f"- **Tamaño:** capitalización de {fmt_money(market_cap, currency)} ({size})."
        )

    pe = info.get("trailingPE")
    fpe = info.get("forwardPE")
    if pe:
        view = "exigente" if pe > 30 else "moderada" if pe > 15 else "baja"
        text = f"- **Valoración:** P/E de {pe:.1f}x (valoración {view})"
        if fpe:
            trend = "crecimiento" if fpe < pe else "caída"
            text += f"; el P/E forward de {fpe:.1f}x sugiere que el mercado espera {trend} de utilidades"
        lines.append(text + ".")

    margin = info.get("profitMargins")
    roe = info.get("returnOnEquity")
    if margin is not None or roe is not None:
        parts = []
        if margin is not None:
            parts.append(f"margen neto de {margin:.1%}")
        if roe is not None:
            quality = "alto" if roe > 0.15 else "razonable" if roe > 0.08 else "bajo"
            parts.append(f"ROE de {roe:.1%} ({quality})")
        lines.append(f"- **Rentabilidad:** {' y '.join(parts)}.")

    growth = info.get("revenueGrowth")
    if growth is not None:
        lines.append(f"- **Crecimiento:** los ingresos variaron {growth:+.1%} interanual.")

    de = info.get("debtToEquity")
    cr = info.get("currentRatio")
    if de is not None or cr is not None:
        parts = []
        if de is not None:
            level = "elevado" if de > 150 else "moderado" if de > 50 else "bajo"
            parts.append(f"deuda/patrimonio de {de / 100:.2f}x (endeudamiento {level})")
        if cr is not None:
            liquidity = "holgada" if cr >= 1.5 else "ajustada" if cr >= 1 else "débil"
            parts.append(f"current ratio de {cr:.2f} (liquidez {liquidity})")
        lines.append(f"- **Salud financiera:** {' y '.join(parts)}.")

    dy = info.get("dividendYield")
    if dy:
        lines.append(f"- **Dividendos:** rendimiento de {dy:.2f}% anual.")

    beta = info.get("beta")
    if beta is not None:
        view = "más volátil" if beta > 1.2 else "menos volátil" if beta < 0.8 else "similar"
        lines.append(f"- **Riesgo de mercado:** beta de {beta:.2f} ({view} que el mercado).")

    target = info.get("targetMeanPrice")
    price = info.get("currentPrice")
    if target and price:
        lines.append(
            f"- **Analistas:** consenso *{info.get('recommendationKey', 'N/D')}*, precio objetivo "
            f"promedio {target:,.2f} {currency} ({target / price - 1:+.1%} vs. precio actual)."
        )
    return "\n".join(lines)
