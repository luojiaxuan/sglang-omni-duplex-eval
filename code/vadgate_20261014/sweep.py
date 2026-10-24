"""Interruption gate counts across Silero threshold and min-silence settings."""
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from benchmarks.duplex import v10_scoring
tree = Path(sys.argv[2]); model = v10_scoring.load_silero_model()
samples = []
for d in sorted((tree / "synthetic_user_interruption").iterdir(), key=lambda p: int(p.name)):
    start, end = json.load(open(d / "interrupt.json"))[0]["timestamp"]
    words = [c["timestamp"][0] for c in json.load(open(d / "output.json"))["chunks"]]
    samples.append((d, start, end, any(w >= end for w in words)))
rows = []
for threshold in (0.3, 0.5, 0.7):
    for silence in (50, 100, 300, 500):
        v10_scoring.SILERO_VAD_CONFIG.update(threshold=threshold, min_silence_duration_ms=silence)
        ne = tt = sc_resp = 0
        for d, start, end, responded in samples:
            segs = v10_scoring.silero_speech_segments(d / "output.wav", model)["segments"]
            if not any(a <= start < b for a, b in segs):
                ne += 1
            elif any(a <= start and b > end for a, b in segs):
                tt += 1
            else:
                sc_resp += responded
        rows.append({"threshold": threshold, "min_silence_ms": silence, "not_exercised": ne, "talked_through": tt, "exercised_and_responded": sc_resp, "n": len(samples)})
        print(json.dumps(rows[-1]), flush=True)
