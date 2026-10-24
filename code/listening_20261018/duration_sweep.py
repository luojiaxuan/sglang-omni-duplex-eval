"""How short a reply can be before UTMOS and voice similarity stop matching the full reply.

Each reply of at least 6 s is cropped around its middle to each duration; the crop's
UTMOS and its similarity with the mean speaker embedding of the other full replies
are compared with the full reply's.
argv: listening directory of a scored repeat, output json.
"""
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile
import torch
import torch.nn.functional as F

from benchmarks.metrics.speaker_similarity import WavLMSpeakerSimilarity
from benchmarks.metrics.speaker_similarity_assets import ensure_speaker_similarity_assets
from benchmarks.metrics.utmos import UTMOSScorer

DURATIONS_S = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0)
MIN_FULL_S = 6.0

listening, out = Path(sys.argv[1]), Path(sys.argv[2])
replies = [
    reply
    for reply in json.loads((listening / "scores.json").read_text())["replies"]
    if reply["wav"] is not None and reply["duration_s"] >= MIN_FULL_S
]
utmos = UTMOSScorer("cuda")
assets = ensure_speaker_similarity_assets()
speaker = WavLMSpeakerSimilarity(
    finetune_checkpoint=assets.finetune_checkpoint, wavlm_base=assets.wavlm_base, device="cuda"
)
full = F.normalize(torch.cat([speaker.embed([str(listening / r["wav"])]).cpu() for r in replies]), dim=-1)
total = full.sum(dim=0)
rows = {str(d): {"utmos_diff": [], "voice_diff": []} for d in DURATIONS_S}
with tempfile.TemporaryDirectory() as scratch:
    for index, reply in enumerate(replies):
        audio, rate = soundfile.read(listening / reply["wav"], dtype="float32")
        centroid = (total - full[index]) / (len(replies) - 1)
        full_voice = float(F.cosine_similarity(full[index], centroid, dim=0)) * 100
        for duration in DURATIONS_S:
            length = int(duration * rate)
            start = (len(audio) - length) // 2
            path = Path(scratch) / "crop.wav"
            soundfile.write(path, audio[start : start + length], rate, subtype="PCM_16")
            crop_utmos = utmos.score_batch([str(path)])[0]
            embedding = F.normalize(speaker.embed([str(path)]).cpu()[0], dim=-1)
            crop_voice = float(F.cosine_similarity(embedding, centroid, dim=0)) * 100
            rows[str(duration)]["utmos_diff"].append(crop_utmos - reply["utmos"])
            rows[str(duration)]["voice_diff"].append(crop_voice - full_voice)
summary = {
    duration: {
        f"{metric}_{stat}": float(fn(values[metric]))
        for metric in ("utmos_diff", "voice_diff")
        for stat, fn in (("mean", np.mean), ("abs_mean", lambda v: np.mean(np.abs(v))), ("sd", np.std))
    }
    for duration, values in rows.items()
}
out.write_text(json.dumps({"replies": len(replies), "durations": summary}, indent=1))
for duration, stats in summary.items():
    print(duration, " ".join(f"{k}={v:.3f}" for k, v in stats.items()))
