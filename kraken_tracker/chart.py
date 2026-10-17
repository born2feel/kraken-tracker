from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # render to file, no display needed (CI, servers)
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import StrMethodFormatter  # noqa: E402

from .models import Candle  # noqa: E402

UP, DOWN, LINE = "#16a34a", "#dc2626", "#2563eb"


def plot(candles: list[Candle], out: Path) -> Path:
    """Close price line with a volume panel below."""
    if not candles:
        raise ValueError("no data to plot")
    label = candles[0].pair
    times = [c.time for c in candles]
    closes = [float(c.close) for c in candles]
    volumes = [float(c.volume) for c in candles]
    colors = [UP if c.close >= c.open else DOWN for c in candles]

    fig, (ax, ax_vol) = plt.subplots(
        2, 1, figsize=(10, 5.5), dpi=120, sharex=True, gridspec_kw={"height_ratios": [3, 1]}
    )
    ax.plot(times, closes, color=LINE, linewidth=1.8)
    ax.fill_between(times, closes, min(closes), color=LINE, alpha=0.08)
    ax.set_title(f"{label} — Kraken, {times[0]:%d %b %Y} – {times[-1]:%d %b %Y}", loc="left")
    ax.annotate(
        f"{closes[-1]:,.2f}",
        xy=(times[-1], closes[-1]),
        xytext=(6, 0),
        textcoords="offset points",
        va="center",
        fontweight="bold",
    )
    ax.yaxis.set_major_formatter(
        StrMethodFormatter("{x:,.0f}" if min(closes) >= 100 else "{x:,.4g}")
    )
    ax_vol.bar(times, volumes, color=colors, width=0.8 * _step_days(candles))
    ax_vol.set_ylabel("Volume")

    for a in (ax, ax_vol):
        a.grid(alpha=0.3)
        a.spines[["top", "right"]].set_visible(False)
    ax_vol.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax_vol.xaxis.get_major_locator()))
    fig.tight_layout()

    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    return out


def _step_days(candles: list[Candle]) -> float:
    """Candle width in days, so volume bars fit any interval."""
    if len(candles) < 2:
        return 1.0
    return (candles[1].time - candles[0].time).total_seconds() / 86400
