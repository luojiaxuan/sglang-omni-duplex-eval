"""Agreement between two judges on the same samples.

ratings: integer 0-5 scores keyed by sample id (FDB v1.0 interruption relevance);
labels: categorical labels keyed by sample id (FDB v1.5 behavior labels).
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def cohen_kappa(a: list, b: list, weights: str | None = None) -> float:
    cats = sorted(set(a) | set(b))
    index = {c: i for i, c in enumerate(cats)}
    k = len(cats)
    if weights == "quadratic":
        w = [[(i - j) ** 2 / (k - 1) ** 2 for j in range(k)] for i in range(k)]
    else:
        w = [[0.0 if i == j else 1.0 for j in range(k)] for i in range(k)]
    n = len(a)
    observed = [[0.0] * k for _ in range(k)]
    for x, y in zip(a, b):
        observed[index[x]][index[y]] += 1 / n
    pa, pb = Counter(a), Counter(b)
    expected = [[pa[ci] / n * pb[cj] / n for cj in cats] for ci in cats]
    num = sum(w[i][j] * observed[i][j] for i in range(k) for j in range(k))
    den = sum(w[i][j] * expected[i][j] for i in range(k) for j in range(k))
    return 1 - num / den


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=("ratings", "labels"), required=True)
    parser.add_argument("--reference", type=Path, required=True, help="JSON {sample_id: value} from the official judge")
    parser.add_argument("--candidate", type=Path, required=True, help="JSON {sample_id: value} from the self-hosted judge")
    args = parser.parse_args()
    ref, cand = load(args.reference), load(args.candidate)
    common = sorted(set(ref) & set(cand))
    a, b = [ref[s] for s in common], [cand[s] for s in common]
    report = {"reference_n": len(ref), "candidate_n": len(cand), "common_n": len(common),
              "exact_agreement": sum(x == y for x, y in zip(a, b)) / len(common)}
    if args.kind == "ratings":
        report.update(
            within_one=sum(abs(x - y) <= 1 for x, y in zip(a, b)) / len(common),
            reference_mean=sum(a) / len(a), candidate_mean=sum(b) / len(b),
            quadratic_kappa=cohen_kappa(a, b, "quadratic"),
            reference_hist=dict(sorted(Counter(a).items())), candidate_hist=dict(sorted(Counter(b).items())),
        )
    else:
        report.update(
            cohen_kappa=cohen_kappa(a, b),
            reference_dist=dict(Counter(a).most_common()), candidate_dist=dict(Counter(b).most_common()),
            confusion={f"{x} -> {y}": n for (x, y), n in Counter(zip(a, b)).most_common() if x != y},
        )
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
