"""Cross-tab the #2331 VAD gates against unified outcomes on one reference tree."""
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from benchmarks.duplex import v10_scoring  # noqa: E402

tree = Path(sys.argv[2])
silence_ms = [int(x) for x in sys.argv[3].split(",")]
model = v10_scoring.load_silero_model()
out = {}
for ms in silence_ms:
    v10_scoring.SILERO_VAD_CONFIG["min_silence_duration_ms"] = ms
    inter = collections.Counter()
    turn = collections.Counter()
    rows = []
    inter_dir = tree / "synthetic_user_interruption"
    for d in sorted(inter_dir.iterdir() if inter_dir.exists() else [], key=lambda p: int(p.name)):
        segs = v10_scoring.silero_speech_segments(d / "output.wav", model)["segments"]
        start, end = json.load(open(d / "interrupt.json"))[0]["timestamp"]
        words = [c["timestamp"][0] for c in json.load(open(d / "output.json"))["chunks"]]
        speaking = any(a <= start < b for a, b in segs)
        through = any(a <= start and b > end for a, b in segs)
        gate = "not_exercised" if not speaking else ("talked_through" if through else "scored")
        after = [w for w in words if w >= end]
        outcome = "response" if after else "no_response"
        lat = min(after) - end if after else None
        inter[(gate, outcome)] += 1
        rows.append({"id": d.name, "gate": gate, "outcome": outcome, "latency": lat})
    for d in sorted((tree / "candor_turn_taking").iterdir(), key=lambda p: int(p.name)):
        segs = v10_scoring.silero_speech_segments(d / "output.wav", model)["segments"]
        e = json.load(open(d / "turn_taking.json"))[0]["timestamp"][0]
        words = [c["timestamp"][0] for c in json.load(open(d / "output.json"))["chunks"]]
        vad_at_e = any(a <= e < b for a, b in segs)
        vad_before_e = any(a < e for a, b in segs)
        asr_early = any(w < e for w in words)
        turn[(f"vad_at_E={vad_at_e}", f"vad_onset_before_E={vad_before_e}", f"asr_early={asr_early}")] += 1
    out[ms] = {
        "interruption": {f"{g}|{o}": n for (g, o), n in sorted(inter.items())},
        "turn_taking": {"|".join(k): n for k, n in sorted(turn.items())},
        "talked_through_latencies": sorted(r["latency"] for r in rows if r["gate"] == "talked_through" and r["latency"] is not None)[:20],
    }
print(json.dumps(out, indent=1))
