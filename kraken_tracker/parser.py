"""Parsing of Kraken public API JSON responses.

Every response has the shape {"error": [...], "result": {...}}. Errors are
reported with HTTP 200, so the "error" list must always be checked.
Numbers come as strings ("81433.70000") and are kept as Decimal.
"""

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from .models import Candle, Ticker


class KrakenError(RuntimeError):
    """Kraken returned an error or an unexpected response."""


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except InvalidOperation as e:
        raise KrakenError(f"bad number: {value!r}") from e


def check_errors(payload: Any) -> dict:
    """Raise KrakenError for API errors, return the "result" object otherwise."""
    if not isinstance(payload, dict):
        raise KrakenError("response is not a JSON object")
    errors = payload.get("error") or []
    if errors:
        raise KrakenError("; ".join(errors))
    result = payload.get("result")
    if not isinstance(result, dict):
        raise KrakenError("response has no result")
    return result


def _single_pair(result: dict) -> Any:
    """Data of the only pair in a result. The key is Kraken's internal pair name."""
    keys = [k for k in result if k != "last"]
    if len(keys) != 1:
        raise KrakenError(f"expected data for one pair, got {len(keys)}")
    return result[keys[0]]


def parse_ticker(payload: Any, pair: str) -> Ticker:
    data = _single_pair(check_errors(payload))
    try:
        return Ticker(
            pair=pair,
            last=_decimal(data["c"][0]),
            bid=_decimal(data["b"][0]),
            ask=_decimal(data["a"][0]),
            open=_decimal(data["o"]),
            # Two-element arrays are [today, last 24 hours].
            low_24h=_decimal(data["l"][1]),
            high_24h=_decimal(data["h"][1]),
            volume_24h=_decimal(data["v"][1]),
            vwap_24h=_decimal(data["p"][1]),
        )
    except (KeyError, IndexError, TypeError) as e:
        raise KrakenError(f"unexpected ticker format: {e!r}") from e


def parse_ohlc(payload: Any, pair: str) -> list[Candle]:
    """Parse OHLC rows: [time, open, high, low, close, vwap, volume, count]."""
    result = check_errors(payload)
    rows = _single_pair(result)
    # "last" is the start time of the last *closed* candle; anything newer is in progress.
    last_closed = int(result.get("last", 0))
    try:
        return [
            Candle(
                pair=pair,
                time=datetime.fromtimestamp(int(row[0]), tz=UTC),
                open=_decimal(row[1]),
                high=_decimal(row[2]),
                low=_decimal(row[3]),
                close=_decimal(row[4]),
                vwap=_decimal(row[5]),
                volume=_decimal(row[6]),
                trades=int(row[7]),
                closed=int(row[0]) <= last_closed,
            )
            for row in rows
        ]
    except (IndexError, TypeError, ValueError) as e:
        raise KrakenError(f"unexpected OHLC format: {e!r}") from e
