# cbr-rates

[![CI](https://github.com/YOUR_USERNAME/cbr-rates/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/cbr-rates/actions/workflows/ci.yml)
[![Update rates](https://github.com/YOUR_USERNAME/cbr-rates/actions/workflows/update.yml/badge.svg)](https://github.com/YOUR_USERNAME/cbr-rates/actions/workflows/update.yml)
![Python](https://img.shields.io/badge/python-3.11%20|%203.12%20|%203.13-blue)

A command-line tool that fetches official exchange rates from the
[Central Bank of Russia API](https://www.cbr.ru/development/SXML/), stores them in CSV
and draws charts. A scheduled GitHub Actions job updates the dataset in this repository
every day.

![USD/RUB chart](data/usd.png)

## Features

- Rates of all currencies for today or any past date
- History of one currency over a period
- Incremental CSV storage: safe to run any number of times, no duplicate rows
- PNG charts, from the API or from the collected data
- Fallback to a mirror when `cbr.ru` is unreachable
- Daily auto-update via GitHub Actions; the data and chart in `data/` are refreshed by a bot
- Tests that never hit the network, CI on Python 3.11–3.13, linting with ruff

## Quick start

```bash
git clone https://github.com/YOUR_USERNAME/cbr-rates.git
cd cbr-rates
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

## Usage

```bash
# Today's rates (all currencies or selected ones)
python -m cbr_rates rates --codes USD,EUR,CNY

# Rates on a specific date
python -m cbr_rates rates --date 2025-01-15 --codes USD

# Daily history of one currency
python -m cbr_rates history EUR --from 2026-09-01 --to 2026-09-30

# Append today's rates to data/rates.csv
python -m cbr_rates update --codes USD,EUR,CNY

# Chart for the last 180 days
python -m cbr_rates plot USD --days 180 -o usd.png
```

After `pip install -e .`, the same commands are available as `cbr-rates <command>`.

## How it works

```
cbr_rates/
├── client.py    HTTP requests to the CBR API, mirror fallback
├── parser.py    XML (windows-1251, comma decimals) → typed objects
├── models.py    Rate / HistoryPoint dataclasses with Decimal values
├── storage.py   CSV merge keyed by (date, currency)
├── chart.py     matplotlib chart
└── cli.py       argparse commands
```

Design decisions:

- **`Decimal`, not `float`.** Money values keep exact precision; `81,5432` stays `81.5432`.
- **Nominal handling.** Some currencies are quoted per 10 or 100 units. Every rate exposes
  `unit_rate`, the price of a single unit, so values are comparable.
- **Date from the response.** On weekends and holidays the CBR returns the rates of the
  nearest working day. The tool stores the date the bank reports, not the date requested.
- **Idempotent storage.** Rows are keyed by `(date, code)`. Re-running `update` replaces a
  row instead of duplicating it, so the scheduled job is safe to retry.
- **No network in tests.** A fake HTTP session returns recorded-shaped XML, so tests are
  fast and deterministic, and also cover the fallback and error paths.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check . && ruff format --check .
```

## License

[MIT](LICENSE)
