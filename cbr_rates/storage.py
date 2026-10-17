"""CSV storage of collected rates: one row per (date, currency)."""

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from .models import Rate

FIELDS = ["date", "code", "name", "nominal", "value", "unit_rate"]


def _row(rate: Rate) -> dict[str, str]:
    return {
        "date": rate.date.isoformat(),
        "code": rate.code,
        "name": rate.name,
        "nominal": str(rate.nominal),
        "value": str(rate.value),
        "unit_rate": str(rate.unit_rate),
    }


def load(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save(path: Path, rates: list[Rate]) -> int:
    """Merge rates into the CSV file. Returns how many rows were added.

    Re-running for the same date is safe: existing (date, code) rows are
    replaced, not duplicated, so a scheduled job can run as often as it likes.
    """
    rows = {(r["date"], r["code"]): r for r in load(path)}
    before = len(rows)
    for rate in rates:
        row = _row(rate)
        rows[(row["date"], row["code"])] = row

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows[key] for key in sorted(rows))
    return len(rows) - before


def series(path: Path, code: str) -> list[tuple[date, Decimal]]:
    """(date, rubles per unit) for one currency, oldest first."""
    code = code.upper()
    return sorted(
        (date.fromisoformat(r["date"]), Decimal(r["unit_rate"]))
        for r in load(path)
        if r["code"] == code
    )
