# SPDX-License-Identifier: Apache-2.0
"""Latency breakdown from replay timing.json files (server-side timeline, seconds).

For each sample the first response is split into: decide (turn decision after the annotated turn
end), llm_ttft (decision to first LLM token), seg (decision to first TTS segment), tts_first
(first segment to first PCM), and total (first audio on the output timeline after the turn end).
Responses decided before the turn end are counted as early takeovers; after_end_decide is the delay
of the first decision at or after the turn end.
"""

import argparse
import json
from pathlib import Path

import numpy as np


def stats(xs):
    xs = np.asarray(xs, dtype=float)
    return {"n": int(xs.size), "mean": round(float(xs.mean()), 3), "p50": round(float(np.percentile(xs, 50)), 3),
            "p90": round(float(np.percentile(xs, 90)), 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dirs", nargs="+", type=Path)
    args = ap.parse_args()
    for out in args.out_dirs:
        rows = [json.loads(p.read_text()) for p in sorted(out.glob("*/timing.json"))]
        parts = {k: [] for k in ("decide", "llm_ttft", "seg", "tts_first", "total", "after_end_decide")}
        early = silent = 0
        lags = [t["turn_lag_p50"] for t in rows if t["turn_lag_p50"] is not None]
        for t in rows:
            rs = t["responses"]
            if not rs:
                silent += 1
                continue
            r = rs[0]
            if r["decide_t"] < t["user_end"]:
                early += 1
            parts["decide"].append(r["decide_t"] - t["user_end"])
            parts["llm_ttft"].append(r["llm_first_token_t"] - r["decide_t"])
            parts["seg"].append(r["first_segment_t"] - r["decide_t"])
            parts["tts_first"].append(r["tts_first_pcm_t"] - r["first_segment_t"])
            parts["total"].append(r["first_audio_t"] - t["user_end"])
            later = [x for x in rs if x["decide_t"] >= t["user_end"]]
            if later:
                parts["after_end_decide"].append(later[0]["decide_t"] - t["user_end"])
        summary = {"dir": str(out), "samples": len(rows), "no_response": silent, "early": early}
        summary.update({k: stats(v) for k, v in parts.items() if v})
        if lags:
            summary["turn_lag_p50"] = stats(lags)
        print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
