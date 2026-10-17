from dataclasses import replace
from decimal import Decimal

from kraken_tracker import storage
from kraken_tracker.parser import parse_ohlc

from .conftest import OHLC_ETH


def candles():
    return parse_ohlc(OHLC_ETH, "ETH/USD")


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "data" / "daily.csv"

    added = storage.save(path, candles())

    assert added == 3
    assert storage.load(path) == candles()


def test_open_candle_is_overwritten_not_duplicated(tmp_path):
    path = tmp_path / "daily.csv"
    storage.save(path, candles())

    # Next day the same candle comes back closed with final values.
    final = replace(candles()[-1], close=Decimal("2450.00"), closed=True)
    added = storage.save(path, [final])

    loaded = storage.load(path)
    assert added == 0
    assert len(loaded) == 3
    assert loaded[-1].close == Decimal("2450.00")
    assert loaded[-1].closed


def test_load_filters_by_pair(tmp_path):
    path = tmp_path / "daily.csv"
    btc = [replace(c, pair="BTC/USD") for c in candles()]
    storage.save(path, candles() + btc)

    assert {c.pair for c in storage.load(path, "BTC/USD")} == {"BTC/USD"}
    assert len(storage.load(path)) == 6


def test_csv_uses_unix_line_endings(tmp_path):
    path = tmp_path / "daily.csv"
    storage.save(path, candles())

    assert b"\r" not in path.read_bytes()


def test_load_missing_file(tmp_path):
    assert storage.load(tmp_path / "nope.csv") == []
