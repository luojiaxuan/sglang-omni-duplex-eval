# SPDX-License-Identifier: Apache-2.0
"""Log the inputs of sglang-omni's semantic VAD (Silero + Smart Turn) on FDB samples.

Before its first end of turn, SemanticTurnDetector scores the audio since the first speech
frame, so the Smart Turn probability at a given point of a silence run does not depend on the
detector's thresholds. This logger records the Silero probability of every 32 ms frame and the
Smart Turn probability every 160 ms of each silence run up to MAX_SILENCE_FRAMES; sweep.py
replays the detector's decision rule on top for any threshold setting.

Needs SGLANG_OMNI_SMART_TURN_MODEL_PATH (smart-turn-v3.2-gpu.onnx).
  python eou_log.py --data <subset>... --out <dir> --shard 0/8
Writes <out>/<subset>/<sample>.json.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import soxr

from sglang_omni.serve.realtime.smart_turn import SmartTurnEOU
from sglang_omni.serve.realtime.vad import VAD_FRAME_SAMPLES, VAD_SAMPLE_RATE, SileroSpeechModel

from fdb_meta import sample_meta

SPEECH_THRESHOLD = 0.5
EOU_EVERY_FRAMES = 5
MAX_SILENCE_FRAMES = 75
MAX_UTTERANCE_SAMPLES = 8 * VAD_SAMPLE_RATE


def run_sample(vad: SileroSpeechModel, eou: SmartTurnEOU, wav: Path) -> dict:
    audio, sr = sf.read(wav, dtype="float32", always_2d=True)
    audio = audio.mean(axis=1)
    if sr != VAD_SAMPLE_RATE:
        audio = soxr.resample(audio, sr, VAD_SAMPLE_RATE).astype(np.float32)
    # note (luojiaxuan): the realtime path receives 16-bit PCM, so quantize the same way.
    audio = np.round(np.clip(audio, -1, 1) * 32767).astype(np.int16).astype(np.float32) / 32768.0
    vad.reset()
    probs, speech, eou_points = [], [], []
    first_speech, silence = None, 0
    for f in range(len(audio) // VAD_FRAME_SAMPLES):
        frame = audio[f * VAD_FRAME_SAMPLES : (f + 1) * VAD_FRAME_SAMPLES]
        p = vad.predict(frame, VAD_SAMPLE_RATE)
        probs.append(round(p, 3))
        speech.append(int(p >= SPEECH_THRESHOLD))
        if speech[-1]:
            first_speech = f if first_speech is None else first_speech
            silence = 0
            continue
        if first_speech is None:
            continue
        silence += 1
        if silence % EOU_EVERY_FRAMES == 0 and silence <= MAX_SILENCE_FRAMES:
            utt = audio[first_speech * VAD_FRAME_SAMPLES : (f + 1) * VAD_FRAME_SAMPLES][-MAX_UTTERANCE_SAMPLES:]
            t = time.perf_counter()
            p_eou = eou.predict(utt, VAD_SAMPLE_RATE)
            eou_points.append([f, silence, round(p_eou, 4), round(time.perf_counter() - t, 4)])
    return {"meta": sample_meta(wav.parent, len(audio) / VAD_SAMPLE_RATE), "frame_s": VAD_FRAME_SAMPLES / VAD_SAMPLE_RATE,
            "first_speech": first_speech, "probs": probs, "speech": speech, "eou": eou_points}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, nargs="+", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--shard", default="0/1")
    args = ap.parse_args()
    k, n = map(int, args.shard.split("/"))
    vad = SileroSpeechModel()
    eou = SmartTurnEOU.load(os.environ["SGLANG_OMNI_SMART_TURN_MODEL_PATH"])
    jobs = [(s.name, d) for s in args.data for d in sorted(p for p in s.iterdir() if (p / "input.wav").exists())]
    for j, (subset, d) in enumerate(jobs):
        if j % n != k:
            continue
        out = args.out / subset / f"{d.name}.json"
        if out.exists():
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".tmp")
        tmp.write_text(json.dumps(run_sample(vad, eou, d / "input.wav")))
        tmp.rename(out)
    print(f"EOU_LOG_DONE shard {k}/{n}")


if __name__ == "__main__":
    main()
