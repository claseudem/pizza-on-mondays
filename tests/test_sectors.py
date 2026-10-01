import pandas as pd

from sectors import SECTORS


def test_sectors_have_required_keys():
    for name, sector in SECTORS.items():
        assert set(sector.keys()) == {"stocks", "start", "end"}, name


def test_sectors_have_at_least_one_ticker():
    for name, sector in SECTORS.items():
        assert len(sector["stocks"]) > 0, name


def test_sectors_tickers_are_unique_within_sector():
    for name, sector in SECTORS.items():
        stocks = sector["stocks"]
        assert len(stocks) == len(set(stocks)), name


def test_sectors_tickers_are_non_empty_strings():
    for sector in SECTORS.values():
        for ticker in sector["stocks"]:
            assert isinstance(ticker, str)
            assert ticker.strip() == ticker
            assert ticker != ""


def test_sectors_date_range_is_valid():
    for name, sector in SECTORS.items():
        start = pd.Timestamp(sector["start"])
        end = pd.Timestamp(sector["end"])
        assert start < end, name
