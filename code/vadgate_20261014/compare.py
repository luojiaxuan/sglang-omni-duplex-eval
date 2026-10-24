"""Old (unified-3) vs gated interruption metrics on one reference export."""
import json, sys
from pathlib import Path
import soundfile
sys.path.insert(0, sys.argv[1])
from benchmarks.duplex import unified_v10 as u

tree = Path(sys.argv[2])
vad = u.load_silero_vad(onnx=True)
old_rows, new_rows = [], []
for d in sorted((tree / "synthetic_user_interruption").iterdir(), key=lambda p: int(p.name)):
    chunks = json.load(open(d / "output.json"))["chunks"]
    starts = [s for s, _ in u.word_spans(chunks)]
    interruption = u.reference_times("user_interruption", json.load(open(d / "interrupt.json")))
    window = u.seconds(soundfile.info(str(d / "output.wav")).duration)
    old_rows.append(u.response_sample(starts, interruption[1], window))
    new_rows.append(u.interruption_sample(starts, u.speech_segments(d / "output.wav", vad), interruption, window))

def brief(metrics):
    out = {}
    for name, m in metrics.items():
        if "median_s" in m:
            out[name] = {k: m[k] for k in ("n", "responses", "median_s", "median_ci95", "p90_s")}
        else:
            out[name] = {"count": m["count"], "n": m["n"], "value": m["value"] and round(m["value"], 3), "ci95": m["ci95"] and [round(x, 3) for x in m["ci95"]]}
    return out

old = u.subset_metrics("turn_taking", [dict(r, outcome=r["outcome"]) for r in old_rows], len(old_rows))
old.pop("early_start_rate")
print(json.dumps({"unified-3": brief(old), "gated": brief(u.subset_metrics("user_interruption", new_rows, len(new_rows)))}, indent=1))
