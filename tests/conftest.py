"""Real-shaped CBR responses and a fake HTTP session, so tests never hit the network."""

import pytest
import requests

# Encoded to windows-1251 below, exactly like the real API does.
DAILY_XML = """<?xml version="1.0" encoding="windows-1251"?>
<ValCurs Date="17.10.2026" name="Foreign Currency Market">
<Valute ID="R01235"><NumCode>840</NumCode><CharCode>USD</CharCode><Nominal>1</Nominal>\
<Name>Доллар США</Name><Value>81,5432</Value><VunitRate>81,5432</VunitRate></Valute>
<Valute ID="R01239"><NumCode>978</NumCode><CharCode>EUR</CharCode><Nominal>1</Nominal>\
<Name>Евро</Name><Value>94,1020</Value><VunitRate>94,102</VunitRate></Valute>
<Valute ID="R01375"><NumCode>156</NumCode><CharCode>CNY</CharCode><Nominal>1</Nominal>\
<Name>Китайский юань</Name><Value>11,3901</Value><VunitRate>11,3901</VunitRate></Valute>
<Valute ID="R01535"><NumCode>578</NumCode><CharCode>NOK</CharCode><Nominal>10</Nominal>\
<Name>Норвежских крон</Name><Value>75,8170</Value><VunitRate>7,5817</VunitRate></Valute>
</ValCurs>
""".encode("windows-1251")

DYNAMIC_XML = """<?xml version="1.0" encoding="windows-1251"?>
<ValCurs ID="R01235" DateRange1="14.10.2026" DateRange2="16.10.2026" name="Dynamic">
<Record Date="16.10.2026" Id="R01235"><Nominal>1</Nominal><Value>81,2000</Value></Record>
<Record Date="14.10.2026" Id="R01235"><Nominal>1</Nominal><Value>80,9000</Value></Record>
<Record Date="15.10.2026" Id="R01235"><Nominal>1</Nominal><Value>81,0500</Value></Record>
</ValCurs>
""".encode("windows-1251")


class FakeResponse:
    def __init__(self, content: bytes = b"", status: int = 200):
        self.content = content
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")


class FakeSession:
    """Answers by URL; records every request for assertions."""

    def __init__(self, routes: dict[str, FakeResponse | Exception]):
        self.routes = routes
        self.headers: dict[str, str] = {}
        self.calls: list[tuple[str, dict | None]] = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        answer = self.routes.get(url, FakeResponse(status=404))
        if isinstance(answer, Exception):
            raise answer
        return answer


@pytest.fixture
def daily_xml() -> bytes:
    return DAILY_XML


@pytest.fixture
def dynamic_xml() -> bytes:
    return DYNAMIC_XML
