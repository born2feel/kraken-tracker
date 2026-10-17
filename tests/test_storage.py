from dataclasses import replace
from datetime import date
from decimal import Decimal

from cbr_rates import storage
from cbr_rates.parser import parse_daily


def test_save_creates_file_and_dirs(tmp_path, daily_xml):
    path = tmp_path / "data" / "rates.csv"

    added = storage.save(path, parse_daily(daily_xml))

    assert added == 4
    rows = storage.load(path)
    assert rows[0].keys() == set(storage.FIELDS)
    assert {r["code"] for r in rows} == {"USD", "EUR", "CNY", "NOK"}


def test_save_twice_does_not_duplicate(tmp_path, daily_xml):
    path = tmp_path / "rates.csv"
    rates = parse_daily(daily_xml)
    storage.save(path, rates)

    # Same day again, e.g. the scheduled job ran twice; the value may be corrected.
    usd = replace(rates[0], value=Decimal("82.0000"))
    added = storage.save(path, [usd])

    assert added == 0
    assert len(storage.load(path)) == 4
    assert storage.series(path, "USD") == [(date(2026, 10, 17), Decimal("82.0000"))]


def test_series_is_sorted_by_date(tmp_path, daily_xml):
    path = tmp_path / "rates.csv"
    usd = parse_daily(daily_xml)[0]
    storage.save(path, [replace(usd, date=date(2026, 10, 20)), usd])

    assert [d.day for d, _ in storage.series(path, "usd")] == [17, 20]


def test_load_missing_file(tmp_path):
    assert storage.load(tmp_path / "nope.csv") == []
