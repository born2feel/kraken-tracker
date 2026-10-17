from datetime import UTC, datetime
from decimal import Decimal

import pytest

from kraken_tracker import cli
from kraken_tracker.cli import fmt_price, main
from kraken_tracker.client import KrakenClient


@pytest.fixture
def client(session):
    return KrakenClient(session, sleep=lambda _: None)


@pytest.fixture(autouse=True)
def frozen_now(monkeypatch):
    """`plot --days` counts back from now; pin it to the date of the recorded data."""

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 10, 17, 12, tzinfo=UTC)

    monkeypatch.setattr(cli, "datetime", FrozenDatetime)


def test_price_table(capsys, client):
    assert main(["price", "BTC/USD", "doge-usd"], client) == 0

    out = capsys.readouterr().out.splitlines()
    assert out[0].split() == ["PAIR", "LAST", "TODAY", "24H", "LOW", "24H", "HIGH", "24H", "VOL"]
    assert out[1].split()[:3] == ["BTC/USD", "81,433.70", "-0.08%"]
    assert out[2].split()[:2] == ["DOGE/USD", "0.080007"]


def test_price_error_prints_no_partial_table(capsys, client):
    assert main(["price", "BTC/USD", "NOPE/USD"], client) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "error: NOPE/USD: EQuery:Unknown asset pair\n"


def test_history_marks_open_candle(capsys, client):
    assert main(["history", "ETH/USD", "--limit", "2"], client) == 0

    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 3  # header + 2 candles
    assert lines[1].startswith("2026-10-16 00:00") and "(open)" not in lines[1]
    assert lines[2].startswith("2026-10-17 00:00") and lines[2].endswith("(open)")


def test_update_then_plot_from_csv(tmp_path, capsys, client):
    csv_path = tmp_path / "daily.csv"
    png = tmp_path / "eth.png"

    assert main(["update", "--pairs", "ETH/USD", "--file", str(csv_path)], client) == 0
    assert "3 new" in capsys.readouterr().out

    args = ["plot", "ETH/USD", "--from-csv", str(csv_path), "--days", "30", "-o", str(png)]
    assert main(args, client) == 0
    assert png.read_bytes().startswith(b"\x89PNG")


def test_plot_with_no_data_in_period(tmp_path, capsys, client):
    args = ["plot", "ETH/USD", "--days", "0", "-o", str(tmp_path / "x.png")]

    assert main(args, client) == 1
    assert "no data to plot" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("value", "expected"),
    [("81433.70000", "81,433.70"), ("1.5", "1.50"), ("0.0800069", "0.080007")],
)
def test_fmt_price(value, expected):
    assert fmt_price(Decimal(value)) == expected
