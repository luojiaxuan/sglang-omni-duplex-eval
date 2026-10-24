"""Cut, click and pitch-shift copies of real completed replies, with the original transcript.

argv: listening directory of a scored repeat, output directory.
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile
import torch
import torchaudio

from benchmarks.duplex.v15_audio import write_json

MIN_DURATION_S = 2.0
MIN_WORDS = 5
LIMIT = 24
CUT_SHARE = 0.4
CLICKS_PER_S = 10
CLICK_SAMPLES = 16
PITCH_STEPS = 4

listening, out = Path(sys.argv[1]), Path(sys.argv[2])
scored = json.loads((listening / "scores.json").read_text())["replies"]
chosen = [
    reply
    for reply in scored
    if reply["status"] == "completed"
    and reply["wav"] is not None
    and reply["duration_s"] >= MIN_DURATION_S
    and reply["word_errors"] is not None
    and reply["word_errors"]["reference_words"] >= MIN_WORDS
][:LIMIT]
rng = np.random.default_rng(0)
records = []
for index, reply in enumerate(chosen):
    audio, rate = soundfile.read(listening / reply["wav"], dtype="float32")
    start = int(len(audio) * (1 - CUT_SHARE) / 2)
    stop = start + int(len(audio) * CUT_SHARE)
    clicked = audio.copy()
    for position in rng.integers(0, len(audio) - CLICK_SAMPLES, int(CLICKS_PER_S * len(audio) / rate)):
        clicked[position : position + CLICK_SAMPLES] += rng.choice([-0.5, 0.5])
    shifted = torchaudio.functional.pitch_shift(torch.from_numpy(audio)[None], rate, PITCH_STEPS)[0].numpy()
    for condition, samples in (
        ("original", audio),
        ("cut", np.concatenate([audio[:start], audio[stop:]])),
        ("clicks", np.clip(clicked, -1, 1)),
        ("pitch", shifted),
    ):
        wav = Path("wav") / condition / f"{index}.wav"
        (out / wav).parent.mkdir(parents=True, exist_ok=True)
        soundfile.write(out / wav, samples, rate, subtype="PCM_16")
        records.append(
            {
                "dataset": "perturb",
                "category": condition,
                "sample_id": reply["sample_id"],
                "variant": reply["variant"],
                "response_id": reply["response_id"],
                "status": "completed",
                "transcript": reply["transcript"],
                "duration_s": len(samples) / rate,
                "wav": str(wav),
            }
        )
write_json(out / "replies.json", {"replies": records})
print(f"{len(chosen)} replies x 4 conditions")
