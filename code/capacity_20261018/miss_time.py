"""Per-session unit misses of one recording, in session start order, with wall-clock start."""
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
            first = json.loads((vdir / "continuous.jsonl").open().readline())
            s = score_session(vdir, manifest["profile"], 0.08)
            late = [round(l, 2) for l in s["unit_lag_s"] if l > 1.0]
            rows.append((first.get("wall_s", first["time_s"]), state["directory"], s["units_expected"], s["units_missed"], max(s["unit_lag_s"], default=0), late))
    rows.sort()
    t0 = rows[0][0]
    print(run_dir.parent.name, "keys", list(first))
    for t, d, e, m, mx, late in rows:
        if m or mx > 0.7:
            print(f"  t+{t - t0:6.1f}s {d:32s} miss {m}/{e} maxlag {mx:.2f} late {late}")
    print("  total miss", sum(r[3] for r in rows), "sessions with miss", sum(1 for r in rows if r[3]))
