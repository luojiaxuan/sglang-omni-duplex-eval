import json, sys, statistics, collections
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from benchmarks.duplex import v10_scoring
tree = Path(sys.argv[2]); model = v10_scoring.load_silero_model()
kinds = collections.Counter(); gaps = []; durs = []
for d in sorted((tree / "synthetic_user_interruption").iterdir(), key=lambda p: int(p.name)):
    segs = v10_scoring.silero_speech_segments(d / "output.wav", model)["segments"]
    start, end = json.load(open(d / "interrupt.json"))[0]["timestamp"]
    if any(a <= start < b for a, b in segs):
        continue
    before = [s for s in segs if s[1] <= start]
    if not before:
        kinds["no speech before onset"] += 1
        first = [s for s in segs if s[0] >= start]
        if first: gaps.append(round(first[0][0] - start, 2))
    else:
        kinds["spoke, stopped before onset"] += 1
        durs.append(round(start - before[-1][1], 2))
print(dict(kinds))
print("silence before onset, s, median/p90:", statistics.median(durs) if durs else None, sorted(durs)[int(0.9*len(durs))-1] if durs else None)
print("first speech after onset when none before, s:", sorted(gaps)[:15])
