"""Where MiniCPM-o's speech onsets fall within its 1 s processing units.

argv: the directory holding minicpmo-g0 .. minicpmo-g7 (each with
repeat-1/v10/reference). For every v1.0 sample, the first transcribed word after
the subset's reference point (turn end E for turn taking, interruption end R for
interruption, session start otherwise) is reduced to its phase within the unit
grid, onset mod 1 s, since units start at session time 0. A model that only emits
audio after a whole unit would put the onsets at one phase; onsets independent of
the unit would spread uniformly. The Rayleigh test checks the circular mean.
For turn taking it also correlates the latency with the slack from E to the next
unit boundary; a reply anchored to that boundary would make the two rise together.
"""

import json
import math
import statistics
import sys
from pathlib import Path

UNIT_S = 1.0
root = Path(sys.argv[1])


def reference_s(sample: Path, subset: str) -> float:
    if subset == "candor_turn_taking":
        return json.loads((sample / "turn_taking.json").read_text())[0]["timestamp"][0]
    elif subset == "synthetic_user_interruption":
        return json.loads((sample / "interrupt.json").read_text())[0]["timestamp"][1]
    else:
        return 0.0


phases: dict[str, list[float]] = {}
slack_latency: list[tuple[float, float]] = []
for tree in sorted(root.glob("minicpmo-g*/repeat-1/v10/reference")):
    for transcript in tree.glob("*/*/output.json"):
        sample, subset = transcript.parent, transcript.parent.parent.name
        words = json.loads(transcript.read_text())["chunks"]
        start = reference_s(sample, subset)
        onsets = [word["timestamp"][0] for word in words if word["timestamp"][0] >= start]
        if onsets:
            phases.setdefault(subset, []).append(onsets[0] % UNIT_S)
            if subset == "candor_turn_taking":
                slack_latency.append((math.ceil(start) - start, onsets[0] - start))
            else:
                pass
        else:
            pass

for subset, values in sorted(phases.items()) + [("all", [v for vs in phases.values() for v in vs])]:
    n = len(values)
    c = sum(math.cos(2 * math.pi * v / UNIT_S) for v in values) / n
    s = sum(math.sin(2 * math.pi * v / UNIT_S) for v in values) / n
    r = math.hypot(c, s)
    mean_phase = (math.atan2(s, c) / (2 * math.pi) * UNIT_S) % UNIT_S
    rayleigh_p = math.exp(-n * r * r)
    bins = [0] * 10
    for v in values:
        bins[min(int(v / UNIT_S * 10), 9)] += 1
    print(f"{subset:28s} n={n:3d} R={r:.2f} mean_phase={mean_phase:.2f}s p~{rayleigh_p:.1e} bins(0.1s)={bins}")

slack, latency = zip(*(pair for pair in slack_latency if pair[1] < 3))
print(f"turn taking: corr(slack to next boundary, latency < 3 s) = {statistics.correlation(slack, latency):.2f}, n={len(slack)}")
