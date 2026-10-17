"""Command line interface: `python -m kraken_tracker <command>`."""

import argparse
import logging
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from . import chart, storage
from .client import KrakenClient
from .pairs import INTERVALS, interval_minutes, normalize
from .parser import KrakenError

DEFAULT_CSV = Path("data/daily.csv")
DEFAULT_PAIRS = ["BTC/USD", "ETH/USD", "SOL/USD"]


def fmt_price(value: Decimal) -> str:
    """Thousands separators for big prices, more digits for cheap coins."""
    return f"{value:,.2f}" if value >= 1 else f"{value:.6f}"


def _pairs(value: str) -> list[str]:
    return [p.strip() for p in value.split(",") if p.strip()]


def cmd_price(args, client: KrakenClient) -> None:
    tickers = [client.ticker(pair) for pair in args.pairs]  # fetch all before printing
    print(
        f"{'PAIR':<10} {'LAST':>14} {'TODAY':>8} {'24H LOW':>14} {'24H HIGH':>14} {'24H VOL':>16}"
    )
    for t in tickers:
        print(
            f"{t.pair:<10} {fmt_price(t.last):>14} {t.change_pct:>+7}% "
            f"{fmt_price(t.low_24h):>14} {fmt_price(t.high_24h):>14} {t.volume_24h:>16,.2f}"
        )


def cmd_history(args, client: KrakenClient) -> None:
    candles = client.ohlc(args.pair, interval_minutes(args.interval))[-args.limit :]
    print(f"{'TIME (UTC)':<17} {'OPEN':>12} {'HIGH':>12} {'LOW':>12} {'CLOSE':>12} {'VOLUME':>14}")
    for c in candles:
        mark = "" if c.closed else "  (open)"
        print(
            f"{c.time:%Y-%m-%d %H:%M} {fmt_price(c.open):>12} {fmt_price(c.high):>12} "
            f"{fmt_price(c.low):>12} {fmt_price(c.close):>12} {c.volume:>14,.2f}{mark}"
        )


def cmd_update(args, client: KrakenClient) -> None:
    for pair in args.pairs:
        candles = client.ohlc(pair, interval_minutes("1d"))
        added = storage.save(args.file, candles)
        print(f"{candles[0].pair}: {len(candles)} daily candles, {added} new -> {args.file}")


def cmd_plot(args, client: KrakenClient) -> None:
    _, label = normalize(args.pair)
    if args.from_csv:
        candles = storage.load(args.from_csv, label)
    else:
        candles = client.ohlc(args.pair, interval_minutes("1d"))
    since = datetime.now(UTC) - timedelta(days=args.days)
    candles = [c for c in candles if c.time >= since]
    print(f"chart saved to {chart.plot(candles, args.output)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kraken-tracker", description="Crypto prices from the Kraken exchange"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("price", help="current prices of trading pairs")
    p.add_argument("pairs", nargs="*", default=DEFAULT_PAIRS, help="e.g. BTC/USD ETH/EUR")
    p.set_defaults(func=cmd_price)

    p = sub.add_parser("history", help="recent candles of one pair")
    p.add_argument("pair", help="e.g. BTC/USD")
    p.add_argument("--interval", default="1d", choices=INTERVALS, help="default: 1d")
    p.add_argument("--limit", type=int, default=14, help="number of candles, default: 14")
    p.set_defaults(func=cmd_history)

    p = sub.add_parser("update", help="save daily candles to a CSV file")
    p.add_argument("--pairs", type=_pairs, default=DEFAULT_PAIRS, help="e.g. BTC/USD,ETH/USD")
    p.add_argument("--file", type=Path, default=DEFAULT_CSV)
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("plot", help="save a PNG chart of one pair")
    p.add_argument("pair", help="e.g. BTC/USD")
    p.add_argument("--days", type=int, default=180, help="period to plot, default: 180")
    p.add_argument("--from-csv", type=Path, help="plot collected data instead of the API")
    p.add_argument("-o", "--output", type=Path, default=Path("chart.png"))
    p.set_defaults(func=cmd_plot)

    return parser


def main(argv: list[str] | None = None, client: KrakenClient | None = None) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args(argv)
    try:
        args.func(args, client or KrakenClient())
    except (KrakenError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0
