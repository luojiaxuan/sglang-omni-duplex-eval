"""Unit misses of each recording binned by session start, 30 s per bin: misses/expected."""
import json, sys
from pathlib import Path
from benchmarks.duplex.run_artifacts import load_run
from benchmarks.duplex.serving import score_session

for run_dir in map(Path, sys.argv[1:]):
    manifest, run, _ = load_run(run_dir)
    rows = []
    for sample in run["samples"]:
        for state in sample["variants"].values():
            vdir = run_dir / state["directory"]
            t = json.loads((vdir / "continuous.jsonl").open().readline())["time_s"]
            s = score_session(vdir, manifest["profile"], 0.08)
            rows.append((t, s["units_missed"], s["units_expected"]))
    t0 = min(r[0] for r in rows)
    bins = {}
    for t, m, e in rows:
        b = int((t - t0) // 30)
        bm, be = bins.get(b, (0, 0))
        bins[b] = (bm + m, be + e)
    print(run_dir.parent.name, " ".join(f"{b*30}s:{m}/{e}" for b, (m, e) in sorted(bins.items())))
