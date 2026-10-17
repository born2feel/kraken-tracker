"""CSV storage of candles: one row per (pair, time)."""

import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from .models import Candle

FIELDS = ["pair", "time", "open", "high", "low", "close", "vwap", "volume", "trades", "closed"]


def _to_row(c: Candle) -> dict[str, str]:
    return {
        "pair": c.pair,
        "time": c.time.isoformat(),
        "open": str(c.open),
        "high": str(c.high),
        "low": str(c.low),
        "close": str(c.close),
        "vwap": str(c.vwap),
        "volume": str(c.volume),
        "trades": str(c.trades),
        "closed": "1" if c.closed else "0",
    }


def _from_row(r: dict[str, str]) -> Candle:
    return Candle(
        pair=r["pair"],
        time=datetime.fromisoformat(r["time"]),
        open=Decimal(r["open"]),
        high=Decimal(r["high"]),
        low=Decimal(r["low"]),
        close=Decimal(r["close"]),
        vwap=Decimal(r["vwap"]),
        volume=Decimal(r["volume"]),
        trades=int(r["trades"]),
        closed=r["closed"] == "1",
    )


def _load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save(path: Path, candles: list[Candle]) -> int:
    """Merge candles into the CSV file. Returns how many new rows were added.

    Rows are keyed by (pair, time), so running the job again never duplicates data.
    It also fixes the last candle: saved while still open, it is overwritten with
    its final values on the next run.
    """
    rows = {(r["pair"], r["time"]): r for r in _load_rows(path)}
    before = len(rows)
    for candle in candles:
        row = _to_row(candle)
        rows[(row["pair"], row["time"])] = row

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        # "\n" instead of the csv default "\r\n": same file on Windows and in CI, clean diffs
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows[key] for key in sorted(rows))
    return len(rows) - before


def load(path: Path, pair: str | None = None) -> list[Candle]:
    """Candles from the file, oldest first, optionally only for one pair label."""
    candles = [_from_row(r) for r in _load_rows(path) if pair is None or r["pair"] == pair]
    return sorted(candles, key=lambda c: (c.pair, c.time))
