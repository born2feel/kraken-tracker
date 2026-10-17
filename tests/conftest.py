"""Responses recorded from the real Kraken API and a fake HTTP session, so tests never
hit the network."""

import pytest
import requests

TICKER_BTC = {
    "error": [],
    "result": {
        # Note the legacy key: asked for BTCUSD, answered as XXBTZUSD.
        "XXBTZUSD": {
            "a": ["81433.70000", "1", "1.000"],
            "b": ["81433.60000", "2", "2.000"],
            "c": ["81433.70000", "0.00039200"],
            "v": ["221.49517497", "1565.24105953"],
            "p": ["81491.82005", "81435.75182"],
            "t": [27530, 112015],
            "l": ["81290.00000", "80705.40000"],
            "h": ["81656.40000", "82376.20000"],
            "o": "81500.90000",
        }
    },
}

TICKER_DOGE = {
    "error": [],
    "result": {
        "XDGUSD": {
            "a": ["0.080002600", "1604", "1604.000"],
            "b": ["0.079999400", "1604", "1604.000"],
            "c": ["0.080006900", "120.18108279"],
            "v": ["7899908.54783536", "24746928.20388359"],
            "p": ["0.080195701", "0.080299815"],
            "t": [2011, 6000],
            "l": ["0.079866000", "0.079262800"],
            "h": ["0.080804300", "0.082310000"],
            "o": "0.080804300",
        }
    },
}

OHLC_ETH = {
    "error": [],
    "result": {
        "XETHZUSD": [
            [1792022400, "2401.10", "2455.00", "2380.00", "2438.96", "2420.50", "20111.5", 50100],
            [1792108800, "2438.96", "2490.84", "2390.35", "2420.22", "2437.44", "23334.35", 53485],
            [1792195200, "2420.23", "2438.00", "2414.34", "2428.44", "2424.02", "13034.31", 10991],
        ],
        "last": 1792108800,
    },
}

UNKNOWN_PAIR = {"error": ["EQuery:Unknown asset pair"]}
RATE_LIMIT = {"error": ["EAPI:Rate limit exceeded"]}


class FakeResponse:
    def __init__(self, payload=None, status: int = 200):
        self.payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error", response=self)

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class FakeSession:
    """Answers by (endpoint, pair) with a queue of responses; records every request."""

    def __init__(self, routes: dict):
        self.routes = {key: list(answers) for key, answers in routes.items()}
        self.headers: dict[str, str] = {}
        self.calls: list[tuple[str, dict]] = []

    def get(self, url, params=None, timeout=None):
        method = url.rsplit("/", 1)[-1]
        self.calls.append((method, params))
        answers = self.routes.get((method, params["pair"]))
        if not answers:
            return FakeResponse(UNKNOWN_PAIR)
        answer = answers.pop(0) if len(answers) > 1 else answers[0]
        if isinstance(answer, Exception):
            raise answer
        return answer


@pytest.fixture
def session():
    return FakeSession(
        {
            ("Ticker", "BTCUSD"): [FakeResponse(TICKER_BTC)],
            ("Ticker", "DOGEUSD"): [FakeResponse(TICKER_DOGE)],
            ("OHLC", "ETHUSD"): [FakeResponse(OHLC_ETH)],
        }
    )
