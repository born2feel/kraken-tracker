from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class Ticker:
    """Current market state of one trading pair."""

    pair: str
    last: Decimal  # last trade price
    bid: Decimal
    ask: Decimal
    open: Decimal  # price at 00:00 UTC today
    low_24h: Decimal
    high_24h: Decimal
    volume_24h: Decimal  # in base currency, e.g. BTC
    vwap_24h: Decimal  # volume weighted average price

    @property
    def change_pct(self) -> Decimal:
        """Change since 00:00 UTC, in percent."""
        return ((self.last - self.open) / self.open * 100).quantize(Decimal("0.01"))

    @property
    def spread(self) -> Decimal:
        return self.ask - self.bid


@dataclass(frozen=True)
class Candle:
    """One OHLC candle. `closed` is False for the current, still changing candle."""

    pair: str
    time: datetime  # candle start, UTC
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    vwap: Decimal
    volume: Decimal
    trades: int
    closed: bool = True
