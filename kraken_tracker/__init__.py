"""Fetch, store and plot crypto market data from the Kraken exchange."""

from .client import KrakenClient
from .models import Candle, Ticker
from .parser import KrakenError

__all__ = ["Candle", "KrakenClient", "KrakenError", "Ticker"]
__version__ = "1.0.0"
