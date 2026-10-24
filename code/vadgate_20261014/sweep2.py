"""unified-4 interruption outcomes and headline rates across Silero settings."""
import collections, json, sys
from pathlib import Path
import soundfile
sys.path.insert(0, sys.argv[1])
from benchmarks.duplex import unified_v10 as u
tree = Path(sys.argv[2]); vad = u.load_silero_vad()
samples = []
for d in sorted((tree / "synthetic_user_interruption").iterdir(), key=lambda p: int(p.name)):
    chunks = json.load(open(d / "output.json"))["chunks"]
    samples.append((d, [s for s, _ in u.word_spans(chunks)],
                    u.reference_times("user_interruption", json.load(open(d / "interrupt.json"))),
                    u.seconds(soundfile.info(str(d / "output.wav")).duration)))
for threshold in (0.3, 0.5, 0.7):
    for silence in (50, 100, 300, 500):
        u.SILERO_VAD_CONFIG.update(threshold=threshold, min_silence_duration_ms=silence)
        rows = [u.interruption_sample(st, u.speech_segments(d / "output.wav", vad), ref, w) for d, st, ref, w in samples]
        m = u.subset_metrics("user_interruption", rows, len(rows))
        print(json.dumps({"threshold": threshold, "min_silence_ms": silence,
                          **collections.Counter(r["outcome"] for r in rows),
                          "response_rate_2s": round(m["response_rate_2s"]["value"], 3),
                          "median_latency_s": m["response_latency_s"]["median_s"]}), flush=True)
