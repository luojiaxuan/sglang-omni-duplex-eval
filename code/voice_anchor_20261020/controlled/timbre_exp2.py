"""Speaker consistency of cascade replies under five ways of speaking them with Qwen3-TTS 1.7B.

cv_per_sentence: CustomVoice Vivian, one request per sentence (what the cascade does).
cv_one_request: CustomVoice Vivian, the whole reply in one request.
base_anchor_per_sentence: Base, every sentence cloned from one fixed anchor clip.
base_anchor_one_request: Base, the whole reply in one request cloned from the anchor.
base_chain: Base, the first sentence cloned from the anchor, each later one from the sentence before it.
base_session_chain: Base, every sentence cloned from the sentence spoken before it, across replies too,
starting from the anchor; shows whether the voice drifts over a session.

The anchor clip is spoken by CustomVoice Vivian, so every condition aims at the same voice.
Per condition: similarity between the sentences of one reply, between sentences of different
replies, and to the anchor (WavLM-large ECAPA, middle 3 s of each sentence), the benchmark's voice
consistency (middle 3 s of each whole reply against the mean of the other replies), plus Whisper WER.

argv: output directory.
"""
import itertools
import json
import re
import sys
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
REPEATS = 6
WINDOW_S = 3.0
ANCHOR_TEXT = "Hi there, it is nice to meet you, and I am happy to help with whatever you need today."
SENTENCES = [
    "Octopuses have three hearts and blue blood due to copper-based hemocyanin.",
    "I don't eat, but I can suggest delicious meals like pasta or sushi.",
    "Time travel is a fascinating idea, but it remains theoretical for now.",
    "The Great Wall of China stretches over twenty thousand kilometers across the north.",
    "That sounds wonderful, tell me more about your trip to the mountains.",
    "Track your spending for a month and set a budget for each category.",
]
REPLIES = [SENTENCES[0:3], SENTENCES[3:6], [SENTENCES[1], SENTENCES[4], SENTENCES[2]]]

out = Path(sys.argv[1])
(out / "wav").mkdir(parents=True, exist_ok=True)
(out / "examples").mkdir(parents=True, exist_ok=True)
client = httpx.Client(timeout=180)


def speak(url, body):
    request = {"input": body.pop("input"), "response_format": "pcm", "stream": True, "language": "English", **body}
    with client.stream("POST", url, json=request) as response:
        response.raise_for_status()
        rate = int(response.headers["X-Sample-Rate"])
        data = b"".join(response.iter_bytes())
    return np.frombuffer(data[: len(data) - len(data) % 2], dtype="<i2").astype("float32") / 32768, rate


def custom_voice(text, **extra):
    return speak(CV_URL, {"model": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice", "voice": "Vivian", "input": text, **extra})


def base_clone(text, ref_path, ref_text):
    return speak(BASE_URL, {"model": "Qwen/Qwen3-TTS-12Hz-1.7B-Base", "input": text,
                            "references": [{"audio_path": str(ref_path), "text": ref_text}]})


def window(audio, rate):
    n = int(WINDOW_S * rate)
    if len(audio) <= n:
        return audio
    start = (len(audio) - n) // 2
    return audio[start:start + n]


def save(audio, rate, name):
    path = out / "wav" / f"{name}.wav"
    sf.write(path, audio, rate)
    return path


def split_by_words(audio, reply):
    words = [len(s.split()) for s in reply]
    bounds = np.cumsum([0] + words) / sum(words) * len(audio)
    return [audio[int(bounds[i]):int(bounds[i + 1])] for i in range(len(reply))]


def speak_reply(condition, reply, anchor_path, name):
    """The reply's audio and its per-sentence parts."""
    if condition == "cv_per_sentence":
        parts = [custom_voice(s)[0] for s in reply]
    elif condition == "cv_one_request":
        whole, _ = custom_voice(" ".join(reply))
        return whole, split_by_words(whole, reply)
    elif condition == "base_anchor_per_sentence":
        parts = [base_clone(s, anchor_path, ANCHOR_TEXT)[0] for s in reply]
    elif condition == "base_anchor_one_request":
        whole, _ = base_clone(" ".join(reply), anchor_path, ANCHOR_TEXT)
        return whole, split_by_words(whole, reply)
    elif condition == "base_chain":
        parts, ref_path, ref_text = [], anchor_path, ANCHOR_TEXT
        for i, s in enumerate(reply):
            audio, rate = base_clone(s, ref_path, ref_text)
            parts.append(audio)
            ref_path, ref_text = save(audio, rate, f"{name}_ref{i}"), s
    elif condition == "base_session_chain":
        parts = []
        for i, s in enumerate(reply):
            audio, rate = base_clone(s, session_reference["path"], session_reference["text"])
            parts.append(audio)
            session_reference.update(path=save(audio, rate, f"{name}_ref{i}"), text=s)
    else:
        raise ValueError(condition)
    return np.concatenate(parts), parts


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
asr = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3-turbo", torch_dtype=torch.float16, device="cuda")


def embed(audio, rate, name):
    path = out / "wav" / f"{name}_win.wav"
    sf.write(path, window(audio, rate), rate)
    return speaker.embed([str(path)]).cpu()[0]


def transcribe(audio, rate):
    audio16 = resample_poly(audio, 16000, rate).astype("float32")
    return asr({"raw": audio16, "sampling_rate": 16000}, generate_kwargs={"language": "english"})["text"]


anchor, rate = custom_voice(ANCHOR_TEXT, seed=1234)
anchor_path = save(anchor, rate, "anchor")
anchor_vector = embed(anchor, rate, "anchor")

session_reference = {"path": anchor_path, "text": ANCHOR_TEXT}
summary = {}
for condition in ("cv_per_sentence", "cv_one_request", "base_anchor_per_sentence", "base_anchor_one_request",
                  "base_chain", "base_session_chain"):
    within, to_anchor, errors, words, segments, whole_vectors = [], [], 0, 0, [], []
    for ri, reply in enumerate(REPLIES):
        for k in range(REPEATS):
            name = f"{condition}_r{ri}_k{k}"
            whole, parts = speak_reply(condition, reply, anchor_path, name)
            sf.write(out / "examples" / f"{name}.wav", whole, rate)
            whole_vectors.append(embed(whole, rate, f"{name}_whole"))
            vectors = [embed(p, rate, f"{name}_p{i}") for i, p in enumerate(parts)]
            within.append(np.mean([cosine(a, b) for a, b in itertools.combinations(vectors, 2)]))
            to_anchor.extend(cosine(v, anchor_vector) for v in vectors)
            segments.extend((ri * REPEATS + k, v) for v in vectors)
            e, n = word_errors(" ".join(reply), transcribe(whole, rate))
            errors, words = errors + e, words + n
    unit = torch.nn.functional.normalize(torch.stack(whole_vectors).float(), dim=-1)
    others = (unit.sum(dim=0, keepdim=True) - unit) / (len(whole_vectors) - 1)
    consistency = 100 * torch.nn.functional.cosine_similarity(unit, others, dim=-1)
    across = [cosine(a, b) for (ra, a), (rb, b) in itertools.combinations(segments, 2) if ra != rb]
    summary[condition] = {
        "within_reply": round(float(np.mean(within)), 1),
        "across_replies": round(float(np.mean(across)), 1),
        "to_anchor": round(float(np.mean(to_anchor)), 1),
        "voice_consistency": round(float(consistency.mean()), 1),
        "wer_percent": round(100 * errors / words, 2),
        "replies": len(within),
    }
    print(condition, summary[condition], flush=True)

(out / "summary.json").write_text(json.dumps(summary, indent=1))
print("EXP_DONE")
