"""Parsing of CBR XML responses.

The CBR API returns XML in windows-1251 with comma as decimal separator:

    <ValCurs Date="17.10.2026" name="Foreign Currency Market">
      <Valute ID="R01235">
        <NumCode>840</NumCode><CharCode>USD</CharCode><Nominal>1</Nominal>
        <Name>Доллар США</Name><Value>81,5432</Value>
      </Valute>
    </ValCurs>
"""

import xml.etree.ElementTree as ET
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from .models import HistoryPoint, Rate


class ParseError(ValueError):
    """Response is not a valid CBR document."""


def _parse_date(text: str) -> date:
    return datetime.strptime(text, "%d.%m.%Y").date()


def _parse_decimal(text: str) -> Decimal:
    try:
        return Decimal(text.strip().replace(",", "."))
    except InvalidOperation as e:
        raise ParseError(f"bad number: {text!r}") from e


def _text(el: ET.Element, tag: str) -> str:
    child = el.find(tag)
    if child is None or child.text is None:
        raise ParseError(f"<{el.tag}> has no <{tag}>")
    return child.text.strip()


def _root(xml: bytes) -> ET.Element:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        raise ParseError(f"invalid XML: {e}") from e
    if root.tag != "ValCurs":
        raise ParseError(f"unexpected root <{root.tag}>")
    return root


def parse_daily(xml: bytes) -> list[Rate]:
    """Parse XML_daily.asp response into rates for all currencies.

    The date is taken from the response, not from the request: on weekends and
    holidays the CBR returns the rates of the nearest working day.
    """
    root = _root(xml)
    if "Date" not in root.attrib:
        raise ParseError("<ValCurs> has no Date attribute")
    on_date = _parse_date(root.attrib["Date"])
    return [
        Rate(
            date=on_date,
            cbr_id=valute.attrib.get("ID", ""),
            code=_text(valute, "CharCode"),
            name=_text(valute, "Name"),
            nominal=int(_text(valute, "Nominal")),
            value=_parse_decimal(_text(valute, "Value")),
        )
        for valute in root.iter("Valute")
    ]


def parse_dynamic(xml: bytes) -> list[HistoryPoint]:
    """Parse XML_dynamic.asp response (one currency over a date range)."""
    root = _root(xml)
    points = [
        HistoryPoint(
            date=_parse_date(record.attrib["Date"]),
            nominal=int(_text(record, "Nominal")),
            value=_parse_decimal(_text(record, "Value")),
        )
        for record in root.iter("Record")
    ]
    return sorted(points, key=lambda p: p.date)
