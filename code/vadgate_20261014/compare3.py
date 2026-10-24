"""unified-4 interruption metrics on one reference export, with a Silero settings sweep."""
import collections, json, sys
from pathlib import Path
import soundfile
sys.path.insert(0, sys.argv[1])
from benchmarks.duplex import unified_v10 as u

tree = Path(sys.argv[2]); vad = u.load_silero_vad()
samples = []
for d in sorted((tree / "synthetic_user_interruption").iterdir(), key=lambda p: int(p.name)):
    chunks = json.load(open(d / "output.json"))["chunks"]
    window = u.seconds(soundfile.info(str(d / "output.wav")).frames / 16000)
    samples.append((d, [s for s, _ in u.word_spans(chunks)],
                    u.reference_times("user_interruption", json.load(open(d / "interrupt.json"))), window))

def brief(m):
    if "median_s" in m:
        return f"median {m['median_s']} {m['median_ci95']} p90 {m['p90_s']} n {m['n']}"
    if "count" in m:
        return f"{m['count']}/{m['n']} = {m['value'] and round(m['value'], 3)} bounds {m['selected_bounds'] and [round(x, 3) for x in m['selected_bounds']]}"
    return f"{m['value'] and round(m['value'], 3)} {m['ci95'] and [round(x, 3) for x in m['ci95']]}"

base = dict(u.SILERO_VAD_CONFIG)
grid = [(0, th, sil) for th in (0.3, 0.5, 0.7) for sil in (50, 100, 300, 500)] + [(30, 0.5, 100)]
for pad, th, sil in grid:
    u.SILERO_VAD_CONFIG.update(base, speech_pad_ms=pad, threshold=th, min_silence_duration_ms=sil)
    rows = [u.interruption_sample(st, u.speech_segments(d / "output.wav", w, vad), ref, w) for d, st, ref, w in samples]
    m = u.subset_metrics("user_interruption", rows, len(rows))
    out = {"pad": pad, "threshold": th, "min_silence_ms": sil, **collections.Counter(r["outcome"] for r in rows),
           "not_exercised_speech_at_end": sum(r["outcome"] == "not_exercised" and r["speech_at_end"] for r in rows),
           "response_rate_2s": round(m["response_rate_2s"]["value"], 3),
           "median_latency_s": m["response_latency_s"]["median_s"],
           "median_stop_s": m["stop_latency_s"]["median_s"],
           "speech_per_interruption_s": round(m["speech_s_per_interruption_s"]["value"], 3),
           "restart_rate": round(m["restart_rate"]["value"], 3)}
    if (pad, th, sil) == (0, 0.5, 100):
        out["default_metrics"] = {k: brief(v) for k, v in m.items()}
    print(json.dumps(out), flush=True)
