"""HTTP client for the Central Bank of Russia public API (no key required).

Docs: https://www.cbr.ru/development/SXML/
"""

import logging
from datetime import date

import requests

from .models import HistoryPoint, Rate
from .parser import parse_daily, parse_dynamic

log = logging.getLogger(__name__)

CBR_DAILY_URL = "https://www.cbr.ru/scripts/XML_daily.asp"
CBR_DYNAMIC_URL = "https://www.cbr.ru/scripts/XML_dynamic.asp"
# Community mirror with the same XML format. cbr.ru sometimes rejects requests
# from foreign IPs (e.g. GitHub Actions runners), the mirror does not.
MIRROR_DAILY_URL = "https://www.cbr-xml-daily.ru/daily_utf8.xml"

DEFAULT_TIMEOUT = 15
# cbr.ru answers 403 to requests without a browser-like User-Agent.
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; cbr-rates/1.0)"}


class CbrError(RuntimeError):
    """Rates could not be fetched."""


def _cbr_date(d: date) -> str:
    return d.strftime("%d/%m/%Y")


class CbrClient:
    def __init__(self, session: requests.Session | None = None, timeout: float = DEFAULT_TIMEOUT):
        self.session = session or requests.Session()
        self.session.headers.update(HEADERS)
        self.timeout = timeout

    def _get(self, url: str, params: dict | None = None) -> bytes:
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise CbrError(f"request to {url} failed: {e}") from e
        return resp.content

    def daily(self, on_date: date | None = None) -> list[Rate]:
        """Rates of all currencies on a date (today if not given)."""
        params = {"date_req": _cbr_date(on_date)} if on_date else None
        try:
            return parse_daily(self._get(CBR_DAILY_URL, params))
        except CbrError:
            # The mirror only serves today's rates.
            if on_date is not None:
                raise
            log.warning("cbr.ru is unavailable, falling back to mirror")
            return parse_daily(self._get(MIRROR_DAILY_URL))

    def history(self, code: str, start: date, end: date) -> list[HistoryPoint]:
        """Rates of one currency (e.g. "USD") for every working day in [start, end]."""
        if start > end:
            raise ValueError("start date is after end date")
        # The history endpoint wants the internal CBR id, so look it up first.
        by_code = {r.code: r for r in self.daily()}
        rate = by_code.get(code.upper())
        if rate is None:
            raise CbrError(f"unknown currency code: {code}")
        xml = self._get(
            CBR_DYNAMIC_URL,
            {"date_req1": _cbr_date(start), "date_req2": _cbr_date(end), "VAL_NM_RQ": rate.cbr_id},
        )
        return parse_dynamic(xml)
