"""Voice similarity of the real replies and of original against pitch-shifted copies,
for each window length that both the UTMOS floor and the voice window take.

argv: listening directory of a scored repeat, perturbation directory, output json.
"""
import json
import sys
from pathlib import Path

import numpy as np

from benchmarks.duplex import listening_scores

WINDOWS_S = (1.0, 1.5, 2.0, 3.0, 4.0)

listening, perturb, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
rows = {}
for window_s in WINDOWS_S:
    listening_scores.SCORED_DURATION_S = window_s
    real = listening_scores.score_replies(listening, "cuda")
    spoken = [reply for reply in real if reply["wav"] is not None]
    voices = [reply["voice_similarity"] for reply in spoken if reply["voice_similarity"] is not None]
    copies = listening_scores.score_replies(perturb, "cuda")
    by_condition = {
        condition: [
            reply["voice_similarity"]
            for reply in copies
            if reply["category"] == condition and reply["voice_similarity"] is not None
        ]
        for condition in ("original", "pitch")
    }
    original, pitch = (np.array(by_condition[name]) for name in ("original", "pitch"))
    pooled_sd = np.sqrt((original.var(ddof=1) + pitch.var(ddof=1)) / 2)
    rows[str(window_s)] = {
        "real_scored": len(voices),
        "real_with_audio": len(spoken),
        "real_mean": float(np.mean(voices)),
        "real_p10": float(np.percentile(voices, 10)),
        "original_mean": float(original.mean()),
        "pitch_mean": float(pitch.mean()),
        "separation_d": float((original.mean() - pitch.mean()) / pooled_sd),
    }
    print(window_s, json.dumps(rows[str(window_s)]))
out.write_text(json.dumps(rows, indent=1))
