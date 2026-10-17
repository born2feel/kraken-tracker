from datetime import UTC, datetime
from decimal import Decimal

import pytest

from kraken_tracker.parser import KrakenError, check_errors, parse_ohlc, parse_ticker

from .conftest import OHLC_ETH, TICKER_BTC, TICKER_DOGE, UNKNOWN_PAIR


def test_parse_ticker_ignores_legacy_pair_name():
    t = parse_ticker(TICKER_BTC, "BTC/USD")

    assert t.pair == "BTC/USD"
    assert t.last == Decimal("81433.70000")
    assert t.spread == Decimal("0.1")
    # 24h values are the second element of each pair
    assert t.low_24h == Decimal("80705.40000")
    assert t.high_24h == Decimal("82376.20000")


def test_change_pct_is_relative_to_todays_open():
    assert parse_ticker(TICKER_BTC, "BTC/USD").change_pct == Decimal("-0.08")
    assert parse_ticker(TICKER_DOGE, "DOGE/USD").change_pct == Decimal("-0.99")


def test_parse_ohlc_marks_open_candle():
    candles = parse_ohlc(OHLC_ETH, "ETH/USD")

    assert len(candles) == 3
    assert candles[0].time == datetime(2026, 10, 15, tzinfo=UTC)
    assert candles[1].close == Decimal("2420.22")
    assert candles[1].trades == 53485
    assert [c.closed for c in candles] == [True, True, False]


def test_check_errors_raises_api_error():
    with pytest.raises(KrakenError, match="Unknown asset pair"):
        check_errors(UNKNOWN_PAIR)


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {"error": []},  # no result
        {"error": [], "result": {"A": {}, "B": {}}},  # more than one pair
        {"error": [], "result": {"XXBTZUSD": {"c": ["abc"]}}},  # missing fields
    ],
)
def test_parse_ticker_rejects_unexpected_shapes(payload):
    with pytest.raises(KrakenError):
        parse_ticker(payload, "BTC/USD")


def test_parse_ohlc_rejects_bad_number():
    payload = {"error": [], "result": {"X": [[1, "1", "2", "0.5", "n/a", "1", "1", 1]]}}
    with pytest.raises(KrakenError, match="bad number"):
        parse_ohlc(payload, "X")
