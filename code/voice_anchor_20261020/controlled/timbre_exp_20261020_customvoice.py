"""Speaker consistency of Qwen3-TTS CustomVoice requests, the way the cascade sends them:
one streaming /v1/audio/speech request per sentence. Repeats of one sentence under several
sampling settings, and three-sentence replies spoken in one request or one per sentence.

argv: output directory.
"""
import hashlib
import itertools
import json
import sys
from pathlib import Path

import httpx
import numpy as np
import soundfile as sf
import torch

from benchmarks.metrics.speaker_similarity import WavLMSpeakerSimilarity
from benchmarks.metrics.speaker_similarity_assets import ensure_speaker_similarity_assets

URL = "http://127.0.0.1:28305/v1/audio/speech"
REPEATS = 8
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
CONDITIONS = {
    "default": {},
    "fixed_seed": {"seed": 1234},
    "temperature_0.3": {"temperature": 0.3},
    "subtalker_greedy": {"subtalker_dosample": False},
}

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
client = httpx.Client(timeout=120)


def speak(text, extra):
    body = {"model": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice", "voice": "Vivian", "input": text,
            "response_format": "pcm", "stream": True, "language": "English", **extra}
    with client.stream("POST", URL, json=body) as response:
        response.raise_for_status()
        rate = int(response.headers["X-Sample-Rate"])
        data = b"".join(response.iter_bytes())
    return np.frombuffer(data[: len(data) - len(data) % 2], dtype="<i2").astype("float32") / 32768, rate


def window(audio, rate):
    n = int(WINDOW_S * rate)
    if len(audio) <= n:
        return audio
    start = (len(audio) - n) // 2
    return audio[start:start + n]


assets = ensure_speaker_similarity_assets()
speaker = WavLMSpeakerSimilarity(finetune_checkpoint=assets.finetune_checkpoint, wavlm_base=assets.wavlm_base, device="cuda")


def embed(audio, rate, name):
    path = out / f"{name}.wav"
    sf.write(path, window(audio, rate), rate)
    return speaker.embed([str(path)]).cpu()[0]


def mean_pairwise(vectors):
    sims = [100 * torch.nn.functional.cosine_similarity(a, b, dim=0).item() for a, b in itertools.combinations(vectors, 2)]
    return float(np.mean(sims)), float(np.min(sims))


summary = {"repeats": {}, "replies": {}}
for cname, extra in CONDITIONS.items():
    within, identical, per_sentence_means = [], 0, []
    sentence_vectors = []
    for si, text in enumerate(SENTENCES):
        vectors, hashes = [], set()
        for k in range(REPEATS):
            audio, rate = speak(text, extra)
            hashes.add(hashlib.sha256(audio.tobytes()).hexdigest())
            vectors.append(embed(audio, rate, f"{cname}_s{si}_r{k}"))
        mean, low = mean_pairwise(vectors)
        within.append(mean)
        identical += len(hashes) == 1
        sentence_vectors.append(vectors[0])
        per_sentence_means.append({"sentence": si, "mean": round(mean, 1), "min": round(low, 1), "distinct_outputs": len(hashes)})
    across, _ = mean_pairwise(sentence_vectors)
    summary["repeats"][cname] = {"same_sentence_mean": round(float(np.mean(within)), 1),
                                 "different_sentences_mean": round(across, 1),
                                 "sentences_with_identical_repeats": identical,
                                 "per_sentence": per_sentence_means}
    print(cname, summary["repeats"][cname]["same_sentence_mean"], summary["repeats"][cname]["different_sentences_mean"], identical, flush=True)

for mode in ("one_request", "per_sentence"):
    scores = []
    for ri, reply in enumerate(REPLIES):
        for k in range(4):
            if mode == "one_request":
                audio, rate = speak(" ".join(reply), {})
                words = [len(s.split()) for s in reply]
                bounds = np.cumsum([0] + words) / sum(words) * len(audio)
                parts = [audio[int(bounds[i]):int(bounds[i + 1])] for i in range(3)]
            else:
                parts = []
                for s in reply:
                    audio, rate = speak(s, {})
                    parts.append(audio)
            vectors = [embed(p, rate, f"{mode}_r{ri}_k{k}_p{i}") for i, p in enumerate(parts)]
            scores.append(mean_pairwise(vectors)[0])
    summary["replies"][mode] = {"segment_similarity_mean": round(float(np.mean(scores)), 1), "n": len(scores)}
    print(mode, summary["replies"][mode], flush=True)

(out / "summary.json").write_text(json.dumps(summary, indent=1))
print("EXP_DONE")
