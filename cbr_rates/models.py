from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Rate:
    """Official CBR exchange rate of one currency on one date."""

    date: date
    cbr_id: str  # internal CBR id, e.g. "R01235"; needed for history requests
    code: str  # ISO letter code, e.g. "USD"
    name: str
    nominal: int  # rate is given for this many units, e.g. 10 for CNY in some years
    value: Decimal  # rubles per `nominal` units

    @property
    def unit_rate(self) -> Decimal:
        """Rubles per 1 unit of currency."""
        return (self.value / self.nominal).quantize(Decimal("0.0001"))


@dataclass(frozen=True)
class HistoryPoint:
    date: date
    nominal: int
    value: Decimal

    @property
    def unit_rate(self) -> Decimal:
        return (self.value / self.nominal).quantize(Decimal("0.0001"))
