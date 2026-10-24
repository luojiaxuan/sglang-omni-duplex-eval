"""Silence inside replies and reply language, per system.

Speech is any 20 ms frame within 35 dB of the reply's loudest frame; a reply's
internal silence is the longest run of other frames between its first and last
speech frames. A transcript is non-English when most of its letters are outside
ASCII, or when it holds a word of a short French/Spanish/German stopword list.
argv: output json, then LABEL=LISTENING_DIR for each system.
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile

FRAME_S = 0.02
RANGE_DB = 35.0
STOPWORDS = {"les", "nous", "est", "une", "des", "el", "los", "las", "por", "der", "die", "und", "ist", "das"}


def shape(path):
    audio, rate = soundfile.read(path, dtype="float32")
    frame = int(FRAME_S * rate)
    frames = audio[: len(audio) // frame * frame].reshape(-1, frame)
    level = 10 * np.log10(np.mean(frames**2, axis=1) + 1e-12)
    speech = level > level.max() - RANGE_DB
    idx = np.flatnonzero(speech)
    if len(idx) == 0:
        return 0.0, 0.0
    inner = speech[idx[0] : idx[-1] + 1]
    longest = run = 0
    for active in inner:
        run = 0 if active else run + 1
        longest = max(longest, run)
    return longest * FRAME_S, speech.mean()


def non_english(text):
    letters = [ch for ch in text if ch.isalpha()]
    if letters and sum(not ch.isascii() for ch in letters) / len(letters) > 0.5:
        return True
    return bool(set(text.lower().replace(",", " ").replace(".", " ").split()) & STOPWORDS)


out = {}
for arg in sys.argv[2:]:
    label, root = arg.split("=", 1)
    replies = json.loads((Path(root) / "scores.json").read_text())["replies"]
    rows = []
    for reply in replies:
        if reply["wav"] is None:
            continue
        silence, ratio = shape(Path(root) / reply["wav"])
        rows.append({
            "sample_id": reply["sample_id"], "variant": reply["variant"], "status": reply["status"],
            "duration_s": reply["duration_s"], "longest_silence_s": silence, "speech_ratio": float(ratio),
            "non_english": non_english(reply["transcript"] or ""), "utmos": reply["utmos"],
            "voice_similarity": reply["voice_similarity"], "transcript": reply["transcript"],
        })
    silences = np.array([r["longest_silence_s"] for r in rows])
    ratios = np.array([r["speech_ratio"] for r in rows])
    foreign = [r for r in rows if r["non_english"]]
    voice_en = [r["voice_similarity"] for r in rows if r["voice_similarity"] is not None and not r["non_english"]]
    voice_xx = [r["voice_similarity"] for r in rows if r["voice_similarity"] is not None and r["non_english"]]
    out[label] = {
        "replies_with_audio": len(rows),
        "longest_silence_s_p50": float(np.median(silences)), "longest_silence_s_p90": float(np.percentile(silences, 90)),
        "replies_with_silence_over_2s": int((silences > 2).sum()), "replies_with_silence_over_5s": int((silences > 5).sum()),
        "speech_ratio_p10": float(np.percentile(ratios, 10)), "speech_ratio_median": float(np.median(ratios)),
        "non_english_replies": len(foreign),
        "voice_similarity_english_mean": float(np.mean(voice_en)) if voice_en else None,
        "voice_similarity_non_english_mean": float(np.mean(voice_xx)) if voice_xx else None,
        "non_english_examples": [r["transcript"] for r in foreign[:8]],
        "longest_silences": sorted(rows, key=lambda r: -r["longest_silence_s"])[:5],
    }
    print(label, json.dumps({k: v for k, v in out[label].items() if k not in ("longest_silences",)}, ensure_ascii=False))
    for r in out[label]["longest_silences"]:
        print("  ", r["sample_id"], r["variant"], r["status"], round(r["duration_s"], 1), "s, silence", round(r["longest_silence_s"], 1), "s, speech", round(r["speech_ratio"], 2), repr((r["transcript"] or "")[:80]))
Path(sys.argv[1]).write_text(json.dumps(out, indent=1, ensure_ascii=False))
