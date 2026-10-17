from datetime import UTC, datetime

import pytest
import requests

from kraken_tracker.client import KrakenClient
from kraken_tracker.parser import KrakenError

from .conftest import RATE_LIMIT, TICKER_BTC, FakeResponse, FakeSession


def make_client(session):
    delays = []
    return KrakenClient(session, sleep=delays.append), delays


def test_ticker_sends_normalized_pair(session):
    client, _ = make_client(session)

    t = client.ticker("btc/usd")

    assert t.pair == "BTC/USD"
    assert session.calls == [("Ticker", {"pair": "BTCUSD"})]
    assert "User-Agent" in session.headers


def test_ohlc_passes_interval_and_since(session):
    client, _ = make_client(session)

    client.ohlc("ETH/USD", 1440, since=datetime(2026, 10, 1, tzinfo=UTC))

    assert session.calls == [("OHLC", {"pair": "ETHUSD", "interval": 1440, "since": 1790812800})]


def test_unknown_pair_is_not_retried_and_names_the_pair(session):
    client, delays = make_client(session)

    with pytest.raises(KrakenError, match="NOPE/USD: EQuery:Unknown asset pair"):
        client.ticker("NOPE/USD")

    assert len(session.calls) == 1
    assert delays == []


@pytest.mark.parametrize(
    "failure",
    [
        FakeResponse(RATE_LIMIT),
        FakeResponse(status=502),
        requests.ConnectionError("connection reset"),
    ],
)
def test_temporary_failures_are_retried_with_backoff(failure):
    session = FakeSession({("Ticker", "BTCUSD"): [failure, failure, FakeResponse(TICKER_BTC)]})
    client, delays = make_client(session)

    assert client.ticker("BTC/USD").pair == "BTC/USD"
    assert delays == [1, 2]


def test_gives_up_after_all_retries():
    session = FakeSession({("Ticker", "BTCUSD"): [FakeResponse(status=503)]})
    client, delays = make_client(session)

    with pytest.raises(KrakenError, match="BTC/USD: Ticker request failed"):
        client.ticker("BTC/USD")

    assert len(session.calls) == 3
    assert delays == [1, 2]


def test_client_error_is_not_retried():
    session = FakeSession({("Ticker", "BTCUSD"): [FakeResponse(status=404)]})
    client, delays = make_client(session)

    with pytest.raises(KrakenError):
        client.ticker("BTC/USD")

    assert delays == []


def test_invalid_json_is_reported():
    session = FakeSession({("Ticker", "BTCUSD"): [FakeResponse(ValueError("not json"))]})
    client, _ = make_client(session)

    with pytest.raises(KrakenError, match="not json"):
        client.ticker("BTC/USD")
