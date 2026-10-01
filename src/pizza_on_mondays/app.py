import pandas as pd
import seaborn as sns
import streamlit as st
import yfinance as yf

from ui import colored_subheader, colored_title

SECTORS = {
    "Oil & Gas": {
        "stocks": ["BP", "CVX", "EC", "SHEL", "SU", "TTE", "XOM"],
        "start": "2020-01-01",
        "end": "2026-12-31",
    },
    "Real Estate": {
        "stocks": [
            "ADC", "AKR", "BRX", "EPRT", "FCPT", "KIM", "KRG", "MAC", "NNN",
            "O", "PECO", "REG", "UE",
        ],
        "start": "2026-01-01",
        "end": "2026-12-31",
    },
    "Criptomonedas": {
        "stocks": ["BTC-USD", "DOGE-USD", "ZEC-USD"],
        "start": "2020-01-01",
        "end": "2026-12-31",
    },
}

SECTOR_ICONS = {
    "Oil & Gas": "🛢️",
    "Real Estate": "🏢",
    "Criptomonedas": "🪙",
}


@st.cache_data
def load_returns(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    data = yf.download(tickers, start=start, end=end)["Close"]
    data = data.ffill()  # NO miedo
    data = data.bfill()  # miedo te crea un lookahead bias
    return data.pct_change().dropna()


def build_summary(returns: pd.DataFrame, momentum_window: int = 21) -> pd.DataFrame:
    """Resume, por activo, los datos más relevantes del período seleccionado."""
    cumulative = (1 + returns).cumprod()
    n_days = len(returns)

    total_return = cumulative.iloc[-1] - 1
    annualized_return = (1 + total_return) ** (252 / n_days) - 1 if n_days > 0 else 0
    annualized_vol = returns.std() * (252 ** 0.5)
    sharpe = annualized_return / annualized_vol.replace(0, pd.NA)

    running_max = cumulative.cummax()
    max_drawdown = (cumulative / running_max - 1).min()

    momentum = (
        (1 + returns.tail(momentum_window)).prod() - 1
        if n_days >= 1
        else pd.Series(0, index=returns.columns)
    )

    summary = pd.DataFrame(
        {
            "Retorno total": total_return,
            "Retorno anualizado": annualized_return,
            "Volatilidad anualizada": annualized_vol,
            "Sharpe (aprox., rf=0)": sharpe,
            "Máx. drawdown": max_drawdown,
            f"Momentum últimos {momentum_window}d": momentum,
        }
    )
    return summary.sort_values("Sharpe (aprox., rf=0)", ascending=False)


def build_recommendation(summary: pd.DataFrame, momentum_window: int = 21) -> str:
    """Genera una nota descriptiva a tener en cuenta, en base a métricas históricas.

    No es asesoramiento financiero: es una lectura rápida de los datos del período
    para usar como punto de partida antes de decidir un movimiento.
    """
    if summary.empty:
        return "No hay datos suficientes en el período seleccionado para generar una recomendación."

    momentum_col = f"Momentum últimos {momentum_window}d"

    best_sharpe = summary["Sharpe (aprox., rf=0)"].idxmax()
    best_momentum = summary[momentum_col].idxmax()
    worst_momentum = summary[momentum_col].idxmin()
    most_volatile = summary["Volatilidad anualizada"].idxmax()
    worst_drawdown = summary["Máx. drawdown"].idxmin()

    lines = [
        f"- **{best_sharpe}** muestra la mejor relación retorno/riesgo del período "
        f"(Sharpe aprox. {summary.loc[best_sharpe, 'Sharpe (aprox., rf=0)']:.2f}), "
        "un candidato a mirar si se busca eficiencia riesgo-retorno.",
        f"- **{best_momentum}** tiene el mejor impulso reciente "
        f"({summary.loc[best_momentum, momentum_col]:+.1%} en los últimos {momentum_window} días hábiles), "
        "lo que podría indicar una tendencia a favor a seguir de cerca.",
        f"- **{worst_momentum}** muestra el impulso más débil "
        f"({summary.loc[worst_momentum, momentum_col]:+.1%} en el mismo período), "
        "vale la pena entender qué lo está frenando antes de sumar exposición.",
        f"- **{most_volatile}** presenta la mayor volatilidad anualizada "
        f"({summary.loc[most_volatile, 'Volatilidad anualizada']:.1%}), por lo que conviene "
        "dimensionar cualquier posición con cautela.",
        f"- **{worst_drawdown}** tuvo la caída máxima más pronunciada del período "
        f"({summary.loc[worst_drawdown, 'Máx. drawdown']:.1%}), un dato clave para el manejo de riesgo.",
    ]
    return "\n".join(lines)


def sectors_page() -> None:
    colored_title("🍕 MoaInvest")

    sector_name = st.selectbox(
        "Sector",
        list(SECTORS.keys()),
        format_func=lambda name: f"{SECTOR_ICONS.get(name, '')} {name}",
    )
    sector = SECTORS[sector_name]

    colored_subheader(f"{SECTOR_ICONS.get(sector_name, '')} {sector_name}")

    col1, col2 = st.columns(2)
    start = col1.date_input(
        "Desde", value=pd.Timestamp(sector["start"]), key=f"start_{sector_name}"
    )
    end = col2.date_input(
        "Hasta", value=pd.Timestamp(sector["end"]), key=f"end_{sector_name}"
    )

    returns = load_returns(sector["stocks"], str(start), str(end))

    colored_subheader("📌 Resumen y recomendación")
    summary = build_summary(returns)
    st.dataframe(
        summary.style.format(
            {
                "Retorno total": "{:.1%}",
                "Retorno anualizado": "{:.1%}",
                "Volatilidad anualizada": "{:.1%}",
                "Sharpe (aprox., rf=0)": "{:.2f}",
                "Máx. drawdown": "{:.1%}",
                summary.columns[-1]: "{:+.1%}",
            }
        )
    )
    st.markdown(build_recommendation(summary))
    st.caption(
        "⚠️ Esto es una lectura descriptiva de datos históricos, no una recomendación "
        "de inversión. Cualquier decisión debe considerar el contexto macro, los "
        "fundamentals de cada compañía y tu propio perfil de riesgo."
    )

    colored_subheader("Retornos diarios")
    st.dataframe(returns)

    colored_subheader("Estadísticas")
    st.dataframe(returns.describe())

    colored_subheader("Retornos acumulados")
    st.line_chart((1 + returns).cumprod())

    colored_subheader("Volatilidad (rolling 21 días, anualizada)")
    st.line_chart(returns.rolling(21).std() * (252 ** 0.5))

    colored_subheader("Dispersión entre activos")
    tickers = st.multiselect(
        "Tickers a comparar",
        options=list(returns.columns),
        default=list(returns.columns[:4]),
        key=f"tickers_{sector_name}",
    )
    if len(tickers) >= 2:
        fig = sns.pairplot(returns[tickers], kind="scatter", plot_kws={"alpha": 0.5})
        st.pyplot(fig.figure)
    else:
        st.info("Elegí al menos dos tickers para ver la dispersión.")


def main() -> None:
    st.set_page_config(page_title="MoaInvest", page_icon="🍕", layout="wide")
    sectors_page()


if __name__ == "__main__":
    main()
