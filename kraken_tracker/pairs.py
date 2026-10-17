"""Trading pair names.

Users type pairs as "BTC/USD", "btc-usd" or "BTCUSD". The Kraken API accepts the
concatenated form ("BTCUSD") but answers under its own legacy name ("XXBTZUSD"),
so responses are matched by position, not by name.
"""

import re

# Intervals supported by the Kraken OHLC endpoint, in minutes.
INTERVALS = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
    "1w": 10080,
    "15d": 21600,
}

_PAIR_RE = re.compile(r"^([A-Za-z0-9]{2,10})[/\-_ ]?([A-Za-z0-9]{2,10})?$")


def normalize(pair: str) -> tuple[str, str]:
    """Return (api_symbol, display_label), e.g. "btc-usd" -> ("BTCUSD", "BTC/USD")."""
    text = pair.strip().upper()
    match = _PAIR_RE.match(text)
    if not match:
        raise ValueError(f"invalid pair: {pair!r}, expected e.g. BTC/USD")
    base, quote = match.groups()
    if quote is None:  # "BTCUSD" without a separator, cannot split reliably
        return base, base
    return base + quote, f"{base}/{quote}"


def interval_minutes(name: str) -> int:
    try:
        return INTERVALS[name]
    except KeyError:
        raise ValueError(
            f"unsupported interval {name!r}, choose one of: {', '.join(INTERVALS)}"
        ) from None
