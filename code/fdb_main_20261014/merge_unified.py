"""Merge per-shard v1.0 unified rows and official results into one table per subset.

argv: the sglang-omni checkout with unified_v10, then the shard reference trees.
Official means are merged with their own weights: takeover rates, frequencies and
JSD by evaluated samples, latency and rating by the samples that took the turn.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from benchmarks.duplex import unified_v10 as u  # noqa: E402
from benchmarks.duplex.v10_dataset import SUBSET_TASKS, SUBSETS  # noqa: E402

trees = [Path(path) for path in sys.argv[2:]]
rows, selected = defaultdict(list), defaultdict(int)
official = defaultdict(lambda: defaultdict(float))
for tree in trees:
    for line in (tree / "unified-samples.jsonl").read_text().splitlines():
        row = json.loads(line)
        selected[row["subset"]] += 1
        rows[row["subset"]] += [row] if row["eligible"] else []
    for subset, entry in json.loads((tree / "summary.json").read_text())["subsets"].items():
        n, result = entry["evaluated"], entry["result"]
        merged = official[subset]
        merged["evaluated"] += n
        take = result.get("Average take turn", result.get("TOR mean"))
        merged["take_sum"] += take * n
        for label in ("Average latency", "Average rating"):
            if label in result:
                merged[label] += result[label] * take * n
            else:
                pass
        for label in ("Frequency mean", "JSD mean"):
            if label in result:
                merged[label] += result[label] * n
            else:
                pass
merged_table = {}
for subset in SUBSETS:
    off = official[subset]
    takes = off["take_sum"]
    reference = {"takeover_rate": takes / off["evaluated"]}
    reference.update({label: off[label] / takes for label in ("Average latency", "Average rating") if label in off})
    reference.update({label: off[label] / off["evaluated"] for label in ("Frequency mean", "JSD mean") if label in off})
    entry = {"selected": selected[subset], "eligible": len(rows[subset]), "official": reference}
    if rows[subset]:
        task = SUBSET_TASKS[subset]
        entry["metrics"] = u.subset_metrics(task, rows[subset], selected[subset])
        if task != "pause_handling":
            entry["min_observable_s"] = min(row["observable_s"] for row in rows[subset])
        else:
            pass
    else:
        pass
    merged_table[subset] = entry
print(json.dumps({"definitions_version": u.DEFINITIONS_VERSION, "subsets": merged_table}, indent=1, default=float))
