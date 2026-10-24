# SPDX-License-Identifier: Apache-2.0
"""Plot sweep.csv per (turn-taking subset, pause subset) pair of one population: timely success within a
deadline against pause hold violations, and premature replies against hold violations; one point per
policy, the upper-left frontier per detector family, stars at the shipped defaults.

  python plot_sweep.py <sweep_dir> [deadline_s]   ->  <sweep_dir>/<turn>__<pause>.png
"""

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PAIRS = [
    ("candor_turn_taking", "candor_pause_handling"),
    ("candor_turn_taking", "synthetic_pause_handling"),
    ("turn_taking", "pause_handling"),
]
COLORS = {"soulx": "tab:red", "soulx-eos": "tab:orange", "semvad": "tab:blue", "silence": "tab:gray"}
DEFAULTS = {"soulx": "margin=0,wait=8", "soulx-eos": "margin=0,wait=8", "semvad": "preset=medium", "silence": "silence_ms=640"}


def frontier(points):
    """Points not dominated in (lower x, higher y)."""
    front, best = [], -1.0
    for x, y, *rest in sorted(points, key=lambda p: (p[0], -p[1])):
        if y > best:
            front.append((x, y, *rest))
            best = y
    return front


def main():
    root = Path(sys.argv[1])
    deadline = sys.argv[2] if len(sys.argv) > 2 else "1"
    rows = list(csv.DictReader(open(root / "sweep.csv")))
    by = {(r["family"], r["policy"], r["subset"]): r for r in rows}
    for turn, pause in PAIRS:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
        for fam, color in COLORS.items():
            pts = []
            for (f, pol, sub), r in by.items():
                if f == fam and sub == turn:
                    p = by[(f, pol, pause)]
                    pts.append((float(p["hold_violation"]), float(r[f"timely_{deadline}s"]), float(r["premature"]), pol))
            axes[0].scatter([p[0] for p in pts], [p[1] for p in pts], s=8, alpha=0.25, color=color)
            axes[1].scatter([p[0] for p in pts], [p[2] for p in pts], s=8, alpha=0.25, color=color, label=fam)
            front = frontier(pts)
            axes[0].plot([p[0] for p in front], [p[1] for p in front], "-o", ms=3, color=color, label=fam)
            d = next(p for p in pts if p[3] == DEFAULTS[fam])
            axes[0].scatter([d[0]], [d[1]], marker="*", s=180, color=color, edgecolor="k", zorder=5)
            axes[1].scatter([d[0]], [d[2]], marker="*", s=180, color=color, edgecolor="k", zorder=5)
        axes[0].set_xlabel(f"{pause}: hold violation (reply inside the annotated pause)")
        axes[0].set_ylabel(f"{turn}: reply audio within {deadline} s of turn end")
        axes[1].set_xlabel(f"{pause}: hold violation")
        axes[1].set_ylabel(f"{turn}: premature reply rate")
        for ax in axes:
            ax.grid(alpha=0.3)
            ax.legend()
        fig.suptitle("stars: SoulX margin 0 / wait 8 (with and without mid-speech complete), semantic VAD medium, silence 640 ms; lines: frontier")
        fig.tight_layout()
        fig.savefig(root / f"{turn}__{pause}.png", dpi=130)
        plt.close(fig)


if __name__ == "__main__":
    main()
