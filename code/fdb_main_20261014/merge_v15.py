"""Merge the v1.5 results of the 8 MiniCPM-o shards into one 498-pair table.

Usage (from a sglang-omni checkout, with its venv):
    python merge_v15.py <dir holding minicpmo-g0 .. minicpmo-g7> <out.json>

Timing pools the per-sample official intervals of every shard and reruns the
runbook's own `describe`, so mean, median and the sample-cluster bootstrap are
computed over all pairs at once. Behavior labels and semantic verdicts are
per-pair counts, so they are summed. Each shard's recomputed timing must equal
its own scores/summary.json before anything is merged.
"""

import json
import sys
from collections import Counter
from pathlib import Path

from benchmarks.duplex.reference_core import C_LABELS
from benchmarks.duplex.reference_summary import cluster_bootstrap, describe

ENGINE = "minicpmo"
SHARDS = [f"minicpmo-g{g}" for g in range(8)]
AXES = ("interaction_handling", "relevance", "grounding", "joint")


def shard_clusters(repeat: Path) -> dict[str, dict[str, list[list[float]]]]:
    """Per category, the stop and response interval lists of each timed overlap session."""
    samples = repeat / "scores" / "engines" / ENGINE / "samples"
    clusters: dict[str, dict[str, list[list[float]]]] = {}
    for sample_id in (repeat / "sample-ids.txt").read_text().split():
        category = sample_id.split("/")[0]
        folder = samples / sample_id
        receipt = folder / "receipts" / "timing-overlap.json"
        if not receipt.exists() or json.loads(receipt.read_text())["status"] != "ok":
            continue
        doc = json.loads((folder / "latency_intervals.json").read_text())
        for group in ("all", category):
            entry = clusters.setdefault(group, {"stop": [], "response": []})
            entry["stop"].append([end - start for start, end in doc["latency_stop_list"]])
            entry["response"].append([end - start for start, end in doc["latency_resp_list"]])
    return clusters


def main() -> None:
    root, out = Path(sys.argv[1]), Path(sys.argv[2])
    pooled: dict[str, dict[str, list[list[float]]]] = {}
    pairs, timed = Counter(), Counter()
    labels: dict[str, Counter] = {}
    semantic: dict[str, dict[str, Counter]] = {}
    seeds = set()
    for shard in SHARDS:
        repeat = root / shard / "repeat-1"
        summary = json.loads((repeat / "scores" / "summary.json").read_text())
        seeds.add((summary["bootstrap"]["replicates"], summary["bootstrap"]["seed"]))
        timing_groups = summary["engines"][ENGINE]
        clusters = shard_clusters(repeat)
        for group, timing in timing_groups.items():
            official = timing["timing_official_overlap"]
            for kind in ("stop", "response"):
                mine = describe(clusters[group][kind], 0, "check")
                theirs = official["official_all_intervals"][kind]
                assert mine["interval_n"] == theirs["interval_n"], (shard, group, kind)
                assert mine["mean_s"] == theirs["mean_s"], (shard, group, kind)
                pooled.setdefault(group, {"stop": [], "response": []})[kind] += clusters[group][kind]
            pairs[group] += official["population"]
            timed[group] += official["status"].get("ok", 0)
        behavior = json.loads((repeat / "judge-qwen" / "summary.json").read_text())
        for group, entry in behavior["engines"][ENGINE].items():
            counter = labels.setdefault(group, Counter())
            for label in C_LABELS:
                counter[label] += entry["valid_label_proportions"][label]["count"]
            counter["valid_n"] += entry["valid_n"]
        verdicts = json.loads((repeat / "semantic-qwen" / "summary.json").read_text())
        for group, axes in verdicts["categories"].items():
            for axis in AXES:
                counter = semantic.setdefault(group, {}).setdefault(axis, Counter())
                for key in ("selected", "accepted", "failed", "unresolved"):
                    counter[key] += axes[axis][key]
    (replicates, seed), = seeds
    result = {"shards": SHARDS, "bootstrap": {"replicates": replicates, "seed": seed}, "categories": {}}
    for group in sorted(pooled):
        label_counts = labels[group]
        valid = label_counts["valid_n"]
        result["categories"][group] = {
            "pairs": pairs[group],
            "timed_overlap_sessions": timed[group],
            "stop": describe(pooled[group]["stop"], replicates, f"{seed}:{ENGINE}:{group}:overlap:stop"),
            "response": describe(pooled[group]["response"], replicates, f"{seed}:{ENGINE}:{group}:overlap:resp"),
            "judged_pairs": valid,
            "labels": {
                label: {
                    "count": label_counts[label],
                    "proportion": label_counts[label] / valid,
                    "bootstrap": cluster_bootstrap(
                        [[1.0 if other == label else 0.0] for other in C_LABELS for _ in range(label_counts[other])],
                        replicates,
                        f"{seed}:{ENGINE}:{group}:{label}",
                    ),
                }
                for label in C_LABELS
            },
            "semantic": {
                axis: {
                    **counts,
                    "quality": counts["accepted"] / (counts["accepted"] + counts["failed"]),
                    "coverage": (counts["accepted"] + counts["failed"]) / counts["selected"],
                    "unresolved_bounds": [
                        counts["accepted"] / counts["selected"],
                        (counts["accepted"] + counts["unresolved"]) / counts["selected"],
                    ],
                }
                for axis, counts in ((axis, dict(semantic[group][axis])) for axis in AXES)
            },
        }
    out.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
