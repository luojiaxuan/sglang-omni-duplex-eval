"""Listening examples for the speaker-embedding clone: the six replies of the listening page, one
request per sentence, each sentence cloned from the anchor's speaker embedding alone, and the
leading silence of every sentence, beside the leading silence of the same sentences cloned with the
anchor's transcript (ICL).

argv: anchor wav, output directory.
"""
import json
import sys
from pathlib import Path

import httpx
import numpy as np
import soundfile as sf

URL = "http://127.0.0.1:28306/v1/audio/speech"
SENTENCES = [
    "Octopuses have three hearts and blue blood due to copper-based hemocyanin.",
    "I don't eat, but I can suggest delicious meals like pasta or sushi.",
    "Time travel is a fascinating idea, but it remains theoretical for now.",
    "The Great Wall of China stretches over twenty thousand kilometers across the north.",
    "That sounds wonderful, tell me more about your trip to the mountains.",
    "Track your spending for a month and set a budget for each category.",
]
REPLIES = [SENTENCES[0:3], SENTENCES[3:6], [SENTENCES[1], SENTENCES[4], SENTENCES[2]]]
SILENCE_DBFS = -40.0
FRAME_S = 0.01

anchor, out = sys.argv[1], Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
client = httpx.Client(timeout=180)


ANCHOR_TEXT = "Hi there, it is nice to meet you, and I am happy to help with whatever you need today."


def speak(text, with_transcript=False):
    reference = {"audio_path": anchor, "text": ANCHOR_TEXT} if with_transcript else {"audio_path": anchor}
    body = {"model": "Qwen/Qwen3-TTS-12Hz-1.7B-Base", "input": text, "response_format": "pcm", "stream": True,
            "language": "English", "references": [reference]}
    with client.stream("POST", URL, json=body) as response:
        response.raise_for_status()
        rate = int(response.headers["X-Sample-Rate"])
        data = b"".join(response.iter_bytes())
    return np.frombuffer(data[: len(data) - len(data) % 2], dtype="<i2").astype("float32") / 32768, rate


def onset_s(audio, rate):
    """Seconds before the first 10 ms frame louder than SILENCE_DBFS."""
    n = int(FRAME_S * rate)
    frames = audio[: len(audio) // n * n].reshape(-1, n)
    loud = np.flatnonzero(20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-12) > SILENCE_DBFS)
    return float(loud[0] * FRAME_S) if len(loud) else float(len(audio) / rate)


onsets, pieces, rate = [], [], None
for k in (0, 1):
    for ri, reply in enumerate(REPLIES):
        parts = []
        for s in reply:
            audio, rate = speak(s)
            onsets.append(onset_s(audio, rate))
            parts.append(audio)
        whole = np.concatenate(parts)
        sf.write(out / f"base_xvector_per_sentence_r{ri}_k{k}.wav", whole, rate)
        pieces += [whole, np.zeros(int(0.8 * rate), dtype="float32")]
sf.write(out / "base_xvector_per_sentence_six_turns.wav", np.concatenate(pieces), rate, subtype="PCM_16")
icl = [onset_s(*speak(s, with_transcript=True)) for k in (0, 1) for reply in REPLIES for s in reply]
summary = {"icl_leading_silence_s_mean": round(float(np.mean(icl)), 3), "icl_leading_silence_s_median": round(float(np.median(icl)), 3),
           "icl_leading_silence_s_max": round(float(np.max(icl)), 3),"sentences": len(onsets), "leading_silence_s_mean": round(float(np.mean(onsets)), 3),
           "leading_silence_s_median": round(float(np.median(onsets)), 3), "leading_silence_s_max": round(float(np.max(onsets)), 3)}
(out / "xvector_examples.json").write_text(json.dumps(summary, indent=1))
print(summary)
print("EXAMPLES_DONE")
