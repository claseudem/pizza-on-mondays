import numpy as np
import pandas as pd
import pytest

from capm import (
    ALL_YEARS,
    EXPECTED_RETURN_COL,
    MARKET_TICKERS,
    RISK_FREE_TICKER,
    SECTOR_ICONS,
    available_years,
    build_capm_expected_returns,
    capm_period,
    first_year,
    load_prices_with_market,
)
from sectors import SECTORS

TODAY = pd.Timestamp("2026-09-30")


def make_prices(returns: pd.Series, start: float = 100.0) -> pd.Series:
    """Serie de precios cuyo pct_change reproduce exactamente `returns`."""
    return start * (1 + returns).cumprod()


@pytest.fixture
def market_returns() -> pd.Series:
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2024-01-01", periods=500)
    return pd.Series(rng.normal(0.0005, 0.01, len(dates)), index=dates)


def annualized_market_return(returns: pd.Series) -> float:
    """E(R_m) como lo anualiza capm_return con compounding=True y frequency=252."""
    return (1 + returns).prod() ** (252 / returns.count()) - 1


# --- constantes ---------------------------------------------------------------


def test_market_tickers_are_invertible_etfs_not_raw_indices():
    for ticker in MARKET_TICKERS.values():
        assert not ticker.startswith("^")


def test_risk_free_ticker_is_13_week_treasury_bill():
    assert RISK_FREE_TICKER == "^IRX"


def test_every_sector_has_an_icon():
    assert set(SECTOR_ICONS) == set(SECTORS)


# --- años y períodos ----------------------------------------------------------


def test_first_year_is_earliest_sector_start():
    expected = min(pd.Timestamp(s["start"]).year for s in SECTORS.values())
    assert first_year() == expected


def test_available_years_starts_with_all_and_goes_newest_to_oldest():
    years = available_years(TODAY)
    assert years[0] == ALL_YEARS
    assert years[1:] == list(range(2026, first_year() - 1, -1))


def test_capm_period_for_a_year_covers_the_whole_year_with_exclusive_end():
    # yfinance excluye `end`: pedir hasta el 1 de enero siguiente incluye el 31/12.
    assert capm_period(2020) == ("2020-01-01", "2021-01-01")


def test_capm_period_for_all_years_goes_from_first_year_through_today():
    start, end = capm_period(ALL_YEARS, TODAY)
    assert start == f"{first_year()}-01-01"
    assert end == "2026-10-01"


# --- build_capm_expected_returns ----------------------------------------------


def test_capm_matches_formula_with_known_beta(market_returns):
    prices = pd.DataFrame(
        {
            "DOBLE": make_prices(2 * market_returns),
            "MITAD": make_prices(0.5 * market_returns),
        }
    )
    market = make_prices(market_returns).to_frame("SPY")
    risk_free = pd.Series(0.03, index=market.index)

    capm = build_capm_expected_returns(prices, market, risk_free)

    mkt = annualized_market_return(market_returns.iloc[1:])
    assert capm.loc["DOBLE", "Beta"] == pytest.approx(2.0)
    assert capm.loc["MITAD", "Beta"] == pytest.approx(0.5)
    assert capm.loc["DOBLE", EXPECTED_RETURN_COL] == pytest.approx(0.03 + 2.0 * (mkt - 0.03))
    assert capm.loc["MITAD", EXPECTED_RETURN_COL] == pytest.approx(0.03 + 0.5 * (mkt - 0.03))


def test_capm_asset_identical_to_market_returns_market_return(market_returns):
    market = make_prices(market_returns).to_frame("SPY")
    prices = pd.DataFrame({"CLON": market["SPY"]})
    risk_free = pd.Series(0.02, index=market.index)

    capm = build_capm_expected_returns(prices, market, risk_free)

    assert capm.loc["CLON", "Beta"] == pytest.approx(1.0)
    assert capm.loc["CLON", EXPECTED_RETURN_COL] == pytest.approx(
        annualized_market_return(market_returns.iloc[1:])
    )


def test_capm_is_sorted_by_expected_return_descending(market_returns):
    prices = pd.DataFrame(
        {
            "BAJA": make_prices(0.3 * market_returns),
            "ALTA": make_prices(1.8 * market_returns),
            "MEDIA": make_prices(1.0 * market_returns),
        }
    )
    market = make_prices(market_returns).to_frame("SPY")
    # Prima de mercado positiva para que más beta implique más retorno esperado.
    risk_free = pd.Series(-1.0, index=market.index)

    capm = build_capm_expected_returns(prices, market, risk_free)

    assert list(capm.index) == ["ALTA", "MEDIA", "BAJA"]
    assert capm[EXPECTED_RETURN_COL].is_monotonic_decreasing


def test_capm_output_columns(market_returns):
    prices = make_prices(market_returns).to_frame("XOM")
    market = make_prices(market_returns).to_frame("SPY")
    risk_free = pd.Series(0.01, index=market.index)

    capm = build_capm_expected_returns(prices, market, risk_free)

    assert list(capm.columns) == ["Beta", EXPECTED_RETURN_COL, "Tasa libre de riesgo", "Desde"]


def test_capm_late_listing_asset_beta_is_not_biased(market_returns):
    """Un activo que empieza a cotizar a mitad del período (como PECO) debe medir
    su beta solo contra el mercado de su propia ventana."""
    # Primera mitad del mercado muy volátil (tipo COVID), segunda mitad tranquila.
    half = len(market_returns) // 2
    market_returns = market_returns.copy()
    market_returns.iloc[:half] *= 5

    late = make_prices(1.5 * market_returns.iloc[half:])
    prices = pd.DataFrame(
        {
            "VIEJO": make_prices(market_returns),
            "NUEVO": late.reindex(market_returns.index),
        }
    )
    market = make_prices(market_returns).to_frame("SPY")
    risk_free = pd.Series(0.02, index=market.index)

    capm = build_capm_expected_returns(prices, market, risk_free)

    assert capm.loc["NUEVO", "Beta"] == pytest.approx(1.5)
    assert capm.loc["NUEVO", "Desde"] == market_returns.index[half].date()
    assert capm.loc["VIEJO", "Desde"] == market_returns.index[0].date()


def test_capm_risk_free_is_mean_over_each_asset_window(market_returns):
    half = len(market_returns) // 2
    late = make_prices(market_returns.iloc[half:])
    prices = pd.DataFrame(
        {
            "VIEJO": make_prices(market_returns),
            "NUEVO": late.reindex(market_returns.index),
        }
    )
    market = make_prices(market_returns).to_frame("SPY")
    # Tasa del 0% en la primera mitad y del 5% en la segunda.
    risk_free = pd.Series(
        [0.0] * half + [0.05] * (len(market_returns) - half), index=market.index
    )

    capm = build_capm_expected_returns(prices, market, risk_free)

    assert capm.loc["NUEVO", "Tasa libre de riesgo"] == pytest.approx(0.05)
    assert capm.loc["VIEJO", "Tasa libre de riesgo"] == pytest.approx(risk_free.mean())


# --- load_prices_with_market ----------------------------------------------------


def make_download(dates, close: dict) -> pd.DataFrame:
    """Imita la salida de yf.download con varios tickers (columnas multi-índice)."""
    return pd.DataFrame({("Close", ticker): values for ticker, values in close.items()}, index=dates)


def test_load_prices_with_market_downloads_assets_market_and_risk_free(mocker):
    dates = pd.bdate_range("2024-01-01", periods=3)
    download = mocker.patch(
        "capm.yf.download",
        return_value=make_download(
            dates,
            {"XOM": [1.0, 2.0, 3.0], "SPY": [1.0, 2.0, 3.0], "^IRX": [5.0, 5.0, 5.0]},
        ),
    )

    load_prices_with_market(["XOM"], "SPY", "2024-01-01", "2024-01-04")

    tickers = download.call_args.args[0]
    assert tickers == ["XOM", "SPY", RISK_FREE_TICKER]
    assert download.call_args.kwargs == {"start": "2024-01-01", "end": "2024-01-04"}


def test_load_prices_with_market_converts_risk_free_from_percent_to_decimal(mocker):
    dates = pd.bdate_range("2024-02-01", periods=2)
    mocker.patch(
        "capm.yf.download",
        return_value=make_download(
            dates, {"CVX": [10.0, 11.0], "QQQ": [20.0, 21.0], "^IRX": [4.03, 5.25]}
        ),
    )

    _, _, risk_free = load_prices_with_market(["CVX"], "QQQ", "2024-02-01", "2024-02-03")

    assert risk_free.tolist() == pytest.approx([0.0403, 0.0525])


def test_load_prices_with_market_keeps_only_market_trading_days(mocker):
    """Las cripto cotizan los fines de semana; esos días se descartan para no
    generar retornos de mercado artificiales en 0."""
    dates = pd.date_range("2024-03-01", periods=4, freq="D")  # vie, sáb, dom, lun
    mocker.patch(
        "capm.yf.download",
        return_value=make_download(
            dates,
            {
                "BTC-USD": [100.0, 101.0, 102.0, 103.0],
                "DIA": [50.0, None, None, 51.0],
                "^IRX": [5.0, None, None, 5.0],
            },
        ),
    )

    prices, market, risk_free = load_prices_with_market(
        ["BTC-USD"], "DIA", "2024-03-01", "2024-03-05"
    )

    expected_dates = [pd.Timestamp("2024-03-01"), pd.Timestamp("2024-03-04")]
    assert list(prices.index) == expected_dates
    assert list(market.index) == expected_dates
    assert list(risk_free.index) == expected_dates
    assert prices["BTC-USD"].tolist() == [100.0, 103.0]
    assert list(market.columns) == ["DIA"]


def test_load_prices_with_market_forward_fills_gaps_without_backfilling(mocker):
    dates = pd.bdate_range("2024-04-01", periods=4)
    mocker.patch(
        "capm.yf.download",
        return_value=make_download(
            dates,
            {
                "PECO": [None, 20.0, None, 22.0],  # todavía no cotizaba el primer día
                "IWM": [1.0, 2.0, 3.0, 4.0],
                "^IRX": [5.0, 5.0, 5.0, 5.0],
            },
        ),
    )

    prices, _, _ = load_prices_with_market(["PECO"], "IWM", "2024-04-01", "2024-04-05")

    # El hueco del medio se arrastra (ffill), pero el inicio no se rellena hacia
    # atrás: eso inventaría precios antes de que el activo existiera.
    assert pd.isna(prices["PECO"].iloc[0])
    assert prices["PECO"].iloc[1:].tolist() == [20.0, 20.0, 22.0]
