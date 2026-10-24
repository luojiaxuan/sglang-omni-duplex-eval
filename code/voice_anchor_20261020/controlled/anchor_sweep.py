"""How the anchored Base path depends on the anchor clip: its length and which take of the voice it is,
plus first-audio latency against CustomVoice, sequential and at 8 concurrent requests.

Anchors are CustomVoice Vivian takes of texts of four lengths (seed 1234), and three takes of the
medium text (seeds 1234, 7, 42). Each anchor speaks 3 replies x 4 repeats one request per sentence.

argv: output directory.
"""
import concurrent.futures
import itertools
import json
import re
import sys
import time
from pathlib import Path

import httpx
import numpy as np
import soundfile as sf
import torch

from scipy.signal import resample_poly
from transformers import pipeline

from benchmarks.metrics.speaker_similarity import WavLMSpeakerSimilarity
from benchmarks.metrics.speaker_similarity_assets import ensure_speaker_similarity_assets

CV_URL = "http://127.0.0.1:28305/v1/audio/speech"
BASE_URL = "http://127.0.0.1:28306/v1/audio/speech"
WINDOW_S = 3.0
SENTENCES = [
    "Octopuses have three hearts and blue blood due to copper-based hemocyanin.",
    "I don't eat, but I can suggest delicious meals like pasta or sushi.",
    "Time travel is a fascinating idea, but it remains theoretical for now.",
    "The Great Wall of China stretches over twenty thousand kilometers across the north.",
    "That sounds wonderful, tell me more about your trip to the mountains.",
    "Track your spending for a month and set a budget for each category.",
]
REPLIES = [SENTENCES[0:3], SENTENCES[3:6], [SENTENCES[1], SENTENCES[4], SENTENCES[2]]]
REPEATS = 4
ANCHOR_TEXTS = {
    "short": "Sure, I can help with that.",
    "medium": "Hi there, it is nice to meet you, and I am happy to help with whatever you need today.",
    "long": "Hi there, it is nice to meet you. I am happy to help with whatever you need today, whether "
            "that is planning a trip, cooking dinner, or just talking through your day.",
    "very_long": "Hi there, it is nice to meet you. I am happy to help with whatever you need today, whether "
                 "that is planning a trip, cooking dinner, or just talking through your day. Take your time, "
                 "ask me anything, and we can figure it out together, one step at a time.",
}
ANCHORS = [("short", 1234), ("medium", 1234), ("long", 1234), ("very_long", 1234), ("medium", 7), ("medium", 42)]

out = Path(sys.argv[1])
(out / "anchors").mkdir(parents=True, exist_ok=True)
(out / "wav").mkdir(parents=True, exist_ok=True)


def window(audio, rate):
    n = int(WINDOW_S * rate)
    if len(audio) <= n:
        return audio
    start = (len(audio) - n) // 2
    return audio[start:start + n]


def normalize(text):
    return re.sub(r"[^a-z0-9' ]", " ", text.lower().replace("-", " ")).split()


def word_errors(reference, hypothesis):
    ref, hyp = normalize(reference), normalize(hypothesis)
    row = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        prev, row[0] = row[0], i
        for j, h in enumerate(hyp, 1):
            prev, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, prev + (r != h))
    return row[-1], len(ref)


def cosine(a, b):
    return 100 * torch.nn.functional.cosine_similarity(a, b, dim=0).item()


assets = ensure_speaker_similarity_assets()
speaker = WavLMSpeakerSimilarity(finetune_checkpoint=assets.finetune_checkpoint, wavlm_base=assets.wavlm_base, device="cuda")
asr = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3-turbo", dtype=torch.float16, device="cuda")


def embed(audio, rate, name):
    path = out / "wav" / f"{name}_win.wav"
    sf.write(path, window(audio, rate), rate)
    return speaker.embed([str(path)]).cpu()[0]


def transcribe(audio, rate):
    audio16 = resample_poly(audio, 16000, rate).astype("float32")
    return asr({"raw": audio16, "sampling_rate": 16000}, generate_kwargs={"language": "english"})["text"]


def timed_speak(url, body):
    """PCM audio, sample rate and seconds to the first audio bytes."""
    request = {"response_format": "pcm", "stream": True, "language": "English", **body}
    start = time.perf_counter()
    first = None
    data = b""
    with httpx.Client(timeout=180) as own:
        with own.stream("POST", url, json=request) as response:
            response.raise_for_status()
            rate = int(response.headers["X-Sample-Rate"])
            for piece in response.iter_bytes():
                if piece and first is None:
                    first = time.perf_counter() - start
                data += piece
    return np.frombuffer(data[: len(data) - len(data) % 2], dtype="<i2").astype("float32") / 32768, rate, first


def cv_body(text, **extra):
    return {"model": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice", "voice": "Vivian", "input": text, **extra}


def base_body(text, ref_path, ref_text):
    return {"model": "Qwen/Qwen3-TTS-12Hz-1.7B-Base", "input": text,
            "references": [{"audio_path": str(ref_path), "text": ref_text}]}


def loo(vectors):
    unit = torch.nn.functional.normalize(torch.stack(vectors).float(), dim=-1)
    others = (unit.sum(dim=0, keepdim=True) - unit) / (len(vectors) - 1)
    return float((100 * torch.nn.functional.cosine_similarity(unit, others, dim=-1)).mean())


summary = {"anchors": {}, "latency": {}}
anchor_files = {}
for name, seed in ANCHORS:
    audio, rate, _ = timed_speak(CV_URL, cv_body(ANCHOR_TEXTS[name], seed=seed))
    path = out / "anchors" / f"{name}_seed{seed}.wav"
    sf.write(path, audio, rate)
    anchor_files[(name, seed)] = path
    anchor_vector = embed(audio, rate, f"anchor_{name}_{seed}")
    within, to_anchor, whole_vectors, segments, firsts, errors, words = [], [], [], [], [], 0, 0
    for ri, reply in enumerate(REPLIES):
        for k in range(REPEATS):
            parts = []
            for s in reply:
                part, rate, first = timed_speak(BASE_URL, base_body(s, path, ANCHOR_TEXTS[name]))
                parts.append(part)
                firsts.append(first)
            whole = np.concatenate(parts)
            tag = f"{name}_{seed}_r{ri}_k{k}"
            vectors = [embed(p, rate, f"{tag}_p{i}") for i, p in enumerate(parts)]
            whole_vectors.append(embed(whole, rate, f"{tag}_whole"))
            within.append(np.mean([cosine(a, b) for a, b in itertools.combinations(vectors, 2)]))
            to_anchor.extend(cosine(v, anchor_vector) for v in vectors)
            segments.extend((ri * REPEATS + k, v) for v in vectors)
            e, n = word_errors(" ".join(reply), transcribe(whole, rate))
            errors, words = errors + e, words + n
    across = [cosine(a, b) for (ra, a), (rb, b) in itertools.combinations(segments, 2) if ra != rb]
    summary["anchors"][f"{name}_seed{seed}"] = {
        "anchor_seconds": round(len(audio) / rate, 2),
        "within_reply": round(float(np.mean(within)), 1),
        "across_replies": round(float(np.mean(across)), 1),
        "to_anchor": round(float(np.mean(to_anchor)), 1),
        "voice_consistency": round(loo(whole_vectors), 1),
        "wer_percent": round(100 * errors / words, 2),
        "first_audio_ms_p50": round(1000 * float(np.median(firsts)), 1),
        "replies": len(within),
    }
    print(name, seed, summary["anchors"][f"{name}_seed{seed}"], flush=True)

sentences = [s for reply in REPLIES for s in reply]
medium = anchor_files[("medium", 1234)]
for label, make in (("customvoice", lambda s: (CV_URL, cv_body(s))),
                    ("base_anchor_medium", lambda s: (BASE_URL, base_body(s, medium, ANCHOR_TEXTS["medium"])))):
    for concurrency in (1, 8):
        jobs = [make(s) for s in sentences * (8 if concurrency == 8 else 3)]
        with concurrent.futures.ThreadPoolExecutor(concurrency) as pool:
            firsts = [r[2] for r in pool.map(lambda job: timed_speak(*job), jobs)]
        summary["latency"][f"{label}_c{concurrency}"] = {
            "first_audio_ms_p50": round(1000 * float(np.median(firsts)), 1),
            "first_audio_ms_p90": round(1000 * float(np.percentile(firsts, 90)), 1),
            "requests": len(firsts),
        }
        print(label, concurrency, summary["latency"][f"{label}_c{concurrency}"], flush=True)

(out / "anchor_sweep.json").write_text(json.dumps(summary, indent=1))
print("SWEEP_DONE")
