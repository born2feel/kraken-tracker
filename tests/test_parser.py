from datetime import date
from decimal import Decimal

import pytest

from cbr_rates.parser import ParseError, parse_daily, parse_dynamic


def test_parse_daily_reads_all_currencies(daily_xml):
    rates = parse_daily(daily_xml)

    assert [r.code for r in rates] == ["USD", "EUR", "CNY", "NOK"]
    usd = rates[0]
    assert usd.date == date(2026, 10, 17)
    assert usd.cbr_id == "R01235"
    assert usd.name == "Доллар США"  # windows-1251 decoded correctly
    assert usd.value == Decimal("81.5432")  # comma decimal separator


def test_unit_rate_divides_by_nominal(daily_xml):
    nok = parse_daily(daily_xml)[-1]

    assert nok.nominal == 10
    assert nok.unit_rate == Decimal("7.5817")


def test_parse_dynamic_sorts_by_date(dynamic_xml):
    points = parse_dynamic(dynamic_xml)

    assert [p.date.day for p in points] == [14, 15, 16]
    assert points[-1].unit_rate == Decimal("81.2000")


@pytest.mark.parametrize(
    "xml",
    [
        b"not xml at all",
        b"<html><body>Service unavailable</body></html>",
        b"<ValCurs><Valute ID='R1'><CharCode>USD</CharCode></Valute></ValCurs>",
    ],
)
def test_parse_daily_rejects_bad_documents(xml):
    with pytest.raises(ParseError):
        parse_daily(xml)


def test_parse_daily_rejects_bad_number():
    xml = (
        b'<ValCurs Date="17.10.2026"><Valute ID="R1"><CharCode>USD</CharCode>'
        b"<Name>X</Name><Nominal>1</Nominal><Value>n/a</Value></Valute></ValCurs>"
    )
    with pytest.raises(ParseError, match="bad number"):
        parse_daily(xml)
