import pandas as pd

from quantstats_report import BENCHMARK_TICKERS, all_sector_tickers, load_price_returns
from sectors import SECTORS


def test_all_sector_tickers_covers_every_sector():
    tickers = all_sector_tickers()
    for sector in SECTORS.values():
        for ticker in sector["stocks"]:
            assert ticker in tickers


def test_all_sector_tickers_is_sorted_and_deduplicated():
    tickers = all_sector_tickers()
    assert tickers == sorted(set(tickers))


def test_benchmark_tickers_are_invertible_etfs_not_raw_indices():
    for ticker in BENCHMARK_TICKERS.values():
        assert not ticker.startswith("^")


def test_load_price_returns_computes_pct_change_from_close(mocker):
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    prices = pd.DataFrame({"Close": [100.0, 110.0, None, 121.0]}, index=dates)
    mocker.patch("quantstats_report.yf.download", return_value=prices)

    result = load_price_returns("XOM", "2024-01-01", "2024-01-04")

    assert result.name == "XOM"
    # el hueco (None) se rellena por ffill antes de calcular el retorno (arrastra el
    # valor anterior, retorno 0 en ese día) en vez de descartar la fila; solo la
    # primerísima fila se pierde por el propio pct_change + dropna.
    assert len(result) == 3
    assert round(result.iloc[0], 4) == 0.1
    assert round(result.iloc[1], 4) == 0.0
    assert round(result.iloc[2], 4) == 0.1


def test_load_price_returns_handles_multiindex_close_column(mocker):
    """yf.download puede devolver columnas multi-índice incluso para un solo ticker."""
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    prices = pd.DataFrame(
        {("Close", "AAPL"): [100.0, 105.0]}, index=dates
    )
    mocker.patch("quantstats_report.yf.download", return_value=prices)

    result = load_price_returns("AAPL", "2024-01-01", "2024-01-02")

    assert len(result) == 1
    assert round(result.iloc[0], 2) == 0.05
