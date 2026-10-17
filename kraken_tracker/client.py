"""HTTP client for the Kraken public REST API (market data, no API key required).

Docs: https://docs.kraken.com/api/docs/rest-api/get-ticker-information
"""

import logging
import time
from collections.abc import Callable
from datetime import datetime

import requests

from .models import Candle, Ticker
from .pairs import normalize
from .parser import KrakenError, check_errors, parse_ohlc, parse_ticker

log = logging.getLogger(__name__)

BASE_URL = "https://api.kraken.com/0/public"
DEFAULT_TIMEOUT = 15
HEADERS = {"User-Agent": "kraken-tracker/1.0"}


def _retryable(error: Exception) -> bool:
    if isinstance(error, requests.ConnectionError | requests.Timeout):
        return True
    if isinstance(error, requests.HTTPError) and error.response is not None:
        return error.response.status_code >= 500 or error.response.status_code == 429
    # Kraken reports rate limiting and temporary outages inside the JSON body.
    return isinstance(error, KrakenError) and (
        "Rate limit" in str(error) or "Unavailable" in str(error) or "Busy" in str(error)
    )


class KrakenClient:
    def __init__(
        self,
        session: requests.Session | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = 3,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.session = session or requests.Session()
        self.session.headers.update(HEADERS)
        self.timeout = timeout
        self.retries = retries
        self._sleep = sleep

    def _get(self, method: str, params: dict) -> dict:
        """GET a public endpoint, retrying temporary failures with exponential backoff."""
        url = f"{BASE_URL}/{method}"
        for attempt in range(1, self.retries + 1):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
                resp.raise_for_status()
                payload = resp.json()
                check_errors(payload)  # here, so that rate-limit errors are retried too
                return payload
            except (requests.RequestException, KrakenError, ValueError) as e:
                if attempt == self.retries or not _retryable(e):
                    if isinstance(e, KrakenError):
                        raise
                    raise KrakenError(f"{method} request failed: {e}") from e
                delay = 2 ** (attempt - 1)
                log.warning("%s failed (%s), retrying in %ss", method, e, delay)
                self._sleep(delay)
        raise AssertionError("unreachable")

    def _get_pair(self, method: str, label: str, params: dict) -> dict:
        try:
            return self._get(method, params)
        except KrakenError as e:
            raise KrakenError(f"{label}: {e}") from e

    def ticker(self, pair: str) -> Ticker:
        symbol, label = normalize(pair)
        return parse_ticker(self._get_pair("Ticker", label, {"pair": symbol}), label)

    def ohlc(self, pair: str, interval: int = 1440, since: datetime | None = None) -> list[Candle]:
        """Candles of one pair, oldest first. Kraken returns at most the last 720 candles."""
        symbol, label = normalize(pair)
        params: dict = {"pair": symbol, "interval": interval}
        if since is not None:
            params["since"] = int(since.timestamp())
        return parse_ohlc(self._get_pair("OHLC", label, params), label)
