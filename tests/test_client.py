from datetime import date

import pytest
import requests

from cbr_rates.client import (
    CBR_DAILY_URL,
    CBR_DYNAMIC_URL,
    MIRROR_DAILY_URL,
    CbrClient,
    CbrError,
)

from .conftest import FakeResponse, FakeSession


def test_daily_sends_date_in_cbr_format(daily_xml):
    session = FakeSession({CBR_DAILY_URL: FakeResponse(daily_xml)})

    CbrClient(session).daily(date(2026, 10, 5))

    assert session.calls == [(CBR_DAILY_URL, {"date_req": "05/10/2026"})]
    assert "User-Agent" in session.headers


def test_daily_falls_back_to_mirror(daily_xml):
    session = FakeSession(
        {
            CBR_DAILY_URL: requests.ConnectionError("timeout"),
            MIRROR_DAILY_URL: FakeResponse(daily_xml),
        }
    )

    rates = CbrClient(session).daily()

    assert len(rates) == 4
    assert [url for url, _ in session.calls] == [CBR_DAILY_URL, MIRROR_DAILY_URL]


def test_no_fallback_for_past_dates():
    # The mirror only knows today's rates, returning them for a past date would be wrong.
    session = FakeSession({CBR_DAILY_URL: FakeResponse(status=503)})

    with pytest.raises(CbrError):
        CbrClient(session).daily(date(2026, 1, 15))

    assert len(session.calls) == 1


def test_history_resolves_currency_id(daily_xml, dynamic_xml):
    session = FakeSession(
        {CBR_DAILY_URL: FakeResponse(daily_xml), CBR_DYNAMIC_URL: FakeResponse(dynamic_xml)}
    )

    points = CbrClient(session).history("usd", date(2026, 10, 14), date(2026, 10, 16))

    assert len(points) == 3
    _, params = session.calls[-1]
    assert params == {"date_req1": "14/10/2026", "date_req2": "16/10/2026", "VAL_NM_RQ": "R01235"}


def test_history_unknown_code(daily_xml):
    session = FakeSession({CBR_DAILY_URL: FakeResponse(daily_xml)})

    with pytest.raises(CbrError, match="unknown currency"):
        CbrClient(session).history("XXX", date(2026, 10, 1), date(2026, 10, 2))


def test_history_rejects_reversed_range():
    with pytest.raises(ValueError):
        CbrClient(FakeSession({})).history("USD", date(2026, 10, 2), date(2026, 10, 1))
