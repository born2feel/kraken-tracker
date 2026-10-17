from datetime import date
from decimal import Decimal
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # render to file, no display needed (CI, servers)
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402


def plot(points: list[tuple[date, Decimal]], code: str, out: Path) -> Path:
    if not points:
        raise ValueError(f"no data to plot for {code}")
    dates = [d for d, _ in points]
    values = [float(v) for _, v in points]

    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=120)
    ax.plot(dates, values, color="#2563eb", linewidth=2)
    ax.fill_between(dates, values, min(values), color="#2563eb", alpha=0.08)
    ax.set_title(f"{code}/RUB — official CBR rate", loc="left", fontsize=13)
    ax.set_ylabel("RUB")
    ax.grid(alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
    ax.annotate(
        f"{values[-1]:.2f}",
        xy=(dates[-1], values[-1]),
        xytext=(6, 0),
        textcoords="offset points",
        va="center",
        fontweight="bold",
    )
    fig.tight_layout()

    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    return out
