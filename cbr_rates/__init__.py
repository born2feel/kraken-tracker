"""Fetch, store and plot official exchange rates of the Central Bank of Russia."""

from .client import CbrClient, CbrError
from .models import HistoryPoint, Rate

__all__ = ["CbrClient", "CbrError", "HistoryPoint", "Rate"]
__version__ = "1.0.0"
