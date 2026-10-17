import pytest

from kraken_tracker.pairs import interval_minutes, normalize


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("BTC/USD", ("BTCUSD", "BTC/USD")),
        ("btc-usd", ("BTCUSD", "BTC/USD")),
        (" eth_eur ", ("ETHEUR", "ETH/EUR")),
        ("SOLUSD", ("SOLUSD", "SOLUSD")),
    ],
)
def test_normalize(raw, expected):
    assert normalize(raw) == expected


@pytest.mark.parametrize("raw", ["", "B", "BTC/USD/EUR", "BTC USD!", "a/b"])
def test_normalize_rejects_garbage(raw):
    with pytest.raises(ValueError):
        normalize(raw)


def test_interval_minutes():
    assert interval_minutes("4h") == 240
    with pytest.raises(ValueError, match="unsupported interval"):
        interval_minutes("7m")
