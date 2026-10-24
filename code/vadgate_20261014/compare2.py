"""unified-3 vs unified-4 interruption metrics on one reference export, plus gap diagnostics."""
import collections, json, statistics, sys
from pathlib import Path
import soundfile
sys.path.insert(0, sys.argv[1])
from benchmarks.duplex import unified_v10 as u

tree = Path(sys.argv[2])
vad = u.load_silero_vad()
old_rows, new_rows, durations, gaps = [], [], [], []
for d in sorted((tree / "synthetic_user_interruption").iterdir(), key=lambda p: int(p.name)):
    chunks = json.load(open(d / "output.json"))["chunks"]
    starts = [s for s, _ in u.word_spans(chunks)]
    onset, end = u.reference_times("user_interruption", json.load(open(d / "interrupt.json")))
    window = u.seconds(soundfile.info(str(d / "output.wav")).duration)
    speech = u.speech_segments(d / "output.wav", vad)
    old_rows.append(u.response_sample(starts, end, window))
    row = u.interruption_sample(starts, speech, (onset, end), window)
    new_rows.append(row)
    durations.append(end - onset)
    if row["outcome"] == "not_exercised" and row["speech_before_onset"]:
        gaps.append(round(onset - max(e for s, e in speech if s < onset), 3))

def q(values, f):
    v = sorted(values); return v[max(0, int(f * len(v)) - 1)]
def brief(metrics):
    out = {}
    for name, m in metrics.items():
        if "median_s" in m:
            out[name] = f"median {m['median_s']} {m['median_ci95']} p90 {m['p90_s']} {m['responses']}/{m['n']}"
        else:
            out[name] = f"{m['count']}/{m['n']} = {m['value'] and round(m['value'], 3)} ci {m['ci95'] and [round(x, 3) for x in m['ci95']]} bounds {m['selected_bounds'] and [round(x, 3) for x in m['selected_bounds']]}"
    return out
old = u.subset_metrics("turn_taking", old_rows, len(old_rows)); old.pop("early_start_rate")
print(json.dumps({
    "outcomes": dict(collections.Counter(r["outcome"] for r in new_rows)),
    "not_exercised_with_speech_before_onset": sum(1 for r in new_rows if r["outcome"] == "not_exercised" and r["speech_before_onset"]),
    "gap_last_speech_to_onset_s": {"min": min(gaps), "p10": q(gaps, .1), "median": statistics.median(gaps), "p90": q(gaps, .9), "under_0.3": sum(g < 0.3 for g in gaps)},
    "interruption_len_s": {"min": round(min(durations), 2), "p10": round(q(durations, .1), 2), "median": round(statistics.median(durations), 2), "p90": round(q(durations, .9), 2)},
    "unified-3": brief(old),
    "unified-4": brief(u.subset_metrics("user_interruption", new_rows, len(new_rows))),
}, indent=1))
