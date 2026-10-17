"""Command line interface: `python -m cbr_rates <command>`."""

import argparse
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

from . import chart, storage
from .client import CbrClient, CbrError
from .models import Rate

DEFAULT_CSV = Path("data/rates.csv")
DEFAULT_CODES = ["USD", "EUR", "CNY"]


def _codes(value: str) -> list[str]:
    return [c.strip().upper() for c in value.split(",") if c.strip()]


def _filter(rates: list[Rate], codes: list[str] | None) -> list[Rate]:
    if not codes:
        return rates
    found = [r for r in rates if r.code in codes]
    missing = set(codes) - {r.code for r in found}
    if missing:
        print(f"warning: unknown codes: {', '.join(sorted(missing))}", file=sys.stderr)
    return found


def cmd_rates(args, client: CbrClient) -> None:
    rates = _filter(client.daily(args.date), args.codes)
    if not rates:
        return
    print(f"CBR rates on {rates[0].date:%d.%m.%Y}\n")
    width = max(len(r.name) for r in rates)
    for r in rates:
        print(f"{r.code}  {r.name:<{width}}  {r.unit_rate:>10}")


def cmd_update(args, client: CbrClient) -> None:
    rates = _filter(client.daily(), args.codes)
    added = storage.save(args.file, rates)
    print(f"{rates[0].date}: saved {len(rates)} rates to {args.file} ({added} new)")


def cmd_history(args, client: CbrClient) -> None:
    for p in client.history(args.code, args.start, args.end):
        print(f"{p.date}  {p.unit_rate}")


def cmd_plot(args, client: CbrClient) -> None:
    if args.from_csv:
        points = storage.series(args.from_csv, args.code)
    else:
        end = date.today()
        history = client.history(args.code, end - timedelta(days=args.days), end)
        points = [(p.date, p.unit_rate) for p in history]
    out = chart.plot(points, args.code.upper(), args.output)
    print(f"chart saved to {out}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cbr-rates", description="Official exchange rates of the Central Bank of Russia"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("rates", help="show rates for a date")
    p.add_argument("--date", type=date.fromisoformat, help="YYYY-MM-DD, default: today")
    p.add_argument("--codes", type=_codes, help="e.g. USD,EUR; default: all currencies")
    p.set_defaults(func=cmd_rates)

    p = sub.add_parser("update", help="append today's rates to a CSV file")
    p.add_argument("--file", type=Path, default=DEFAULT_CSV)
    p.add_argument("--codes", type=_codes, default=None, help="default: all currencies")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("history", help="rates of one currency over a period")
    p.add_argument("code", help="e.g. USD")
    p.add_argument("--from", dest="start", type=date.fromisoformat, required=True)
    p.add_argument("--to", dest="end", type=date.fromisoformat, default=date.today())
    p.set_defaults(func=cmd_history)

    p = sub.add_parser("plot", help="save a PNG chart of one currency")
    p.add_argument("code", help="e.g. USD")
    p.add_argument("--days", type=int, default=90, help="period to plot, default: 90")
    p.add_argument("--from-csv", type=Path, help="plot collected data instead of the API")
    p.add_argument("-o", "--output", type=Path, default=Path("chart.png"))
    p.set_defaults(func=cmd_plot)

    return parser


def main(argv: list[str] | None = None, client: CbrClient | None = None) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args(argv)
    try:
        args.func(args, client or CbrClient())
    except (CbrError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0
