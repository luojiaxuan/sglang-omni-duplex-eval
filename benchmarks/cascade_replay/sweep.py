# SPDX-License-Identifier: Apache-2.0
"""Latency vs. takeover trade-off of turn detectors, from the logs of turn_log.py and eou_log.py.

Each policy is replayed on the logged per-chunk scores to find its first reply commitment in every
sample. Up to that commitment the logged trajectory is the one the policy would have produced (see
the two loggers), so the committing chunk is exact; later replies are not simulated, and audio
onset is modelled, not measured:
  commit time  SoulX: serial processing of 160 ms chunks, F_k = max(arrival_k, F_{k-1}) + compute_k,
               plus the full-buffer ASR SoulX runs when it replies (TERMINAL_ASR_S, measured in replay).
               Semantic VAD and silence: the 32 ms frame decision is emitted when its 160 ms packet has
               arrived and, for semantic VAD, once the Smart Turn score is ready.
  onset        commit time + a fixed LLM+TTS delay per language (BACKEND_S, oracle replay P50).
Metrics:
  turn-taking  premature (onset before the annotated turn end E), miss (no commitment), timely success
               G(d) = share of all samples with E <= onset <= E + d (premature and missed count as
               failures), and the conditional on-time latency quantiles for reference;
  pause        takeover (any commitment in the sample, the event FDB's scorer can count) and
               hold_violation (a commitment inside the annotated pause, up to PAUSE_SLACK_S after it).

Families:
  soulx     reply at the end-of-speech decision if logit(complete) - logit(incomplete) > margin,
            otherwise after `wait` further idle chunks (SoulX default: margin 0, wait 8), and whenever the
            argmax state is <|user_complete|> elsewhere (also SoulX's behaviour); margin=inf is the
            SoulX-state timeout
  soulx-eos the same without the reply on an argmax <|user_complete|> outside the end-of-speech decision,
            i.e. replies only at or after a pause; the logger's own trajectory, so equally exact
  semvad    sglang-omni SemanticTurnDetector: Smart Turn scored once after 160 ms of silence, then the
            required silence depends on the score tier (presets low/medium/high, plus a one-tier grid)
  silence   Silero VAD only: reply after a fixed silence

SoulX fills its buffers with random noise on every reset and its decisions on near-silent chunks depend
on it, so a SoulX log is one draw; with several --soulx logs (different seeds) the SoulX metrics are
averaged over draws and summary.json reports how often the default policy commits on the same chunk.

  python sweep.py --soulx <dir>... --eou <dir> --data-counts <json> --out <dir> [--calib <replay out dir>]
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

SUBSET_LANG = {
    "candor_turn_taking": "en",
    "candor_pause_handling": "en",
    "synthetic_pause_handling": "en",
    "turn_taking": "zh",
    "pause_handling": "zh",
}
BACKEND_S = {"en": 0.041, "zh": 0.054}
# note (luojiaxuan): median extra processing of SoulX's replying chunk over its other chunks in the 10-04
# turn-taking replays (EN 312, ZH 232 replies).
TERMINAL_ASR_S = {"en": 0.049, "zh": 0.093}
PACKET_S = 0.16
SEMVAD_PRESETS = {
    "low": (0.92, 0.99, 1200, 500, 3000),
    "medium": (0.88, 0.97, 640, 250, 2000),
    "high": (0.80, 0.93, 320, 200, 1200),
}
CANDIDATE_MS = 160
# note (luojiaxuan): a commitment this soon after the annotated pause ends is still a reaction to it.
PAUSE_SLACK_S = 0.2
FRAME_MS = 32
DEADLINES_S = (0.5, 1.0, 2.0)


@dataclass
class Sample:
    subset: str
    sid: str
    task: str
    user_end: float
    duration: float
    pause: list[float] | None


def load_soulx(root: Path) -> dict[tuple[str, str], tuple[Sample, list[dict]]]:
    out = {}
    for f in sorted(root.glob("*/*.jsonl")):
        rows = [json.loads(line) for line in f.read_text().splitlines()]
        meta = rows[0]["meta"]
        s = Sample(f.parent.name, f.stem, meta["task"], meta["user_end"], meta["duration"], meta.get("pause"))
        finish = 0.0
        for r in rows[1:]:
            finish = max(r["t"], finish) + r["compute"]
            r["ready"] = finish
        out[(s.subset, s.sid)] = (s, [r for r in rows[1:] if "logits" in r])
    return out


def load_eou(root: Path) -> dict[tuple[str, str], tuple[Sample, dict]]:
    out = {}
    for f in sorted(root.glob("*/*.json")):
        d = json.loads(f.read_text())
        meta = d["meta"]
        s = Sample(f.parent.name, f.stem, meta["task"], meta["user_end"], meta["duration"], meta.get("pause"))
        d["eou_at"] = {fr: (p, c) for fr, _, p, c in d["eou"]}
        out[(s.subset, s.sid)] = (s, d)
    return out


def on_packet(t: float) -> float:
    return math.ceil(round(t / PACKET_S, 6)) * PACKET_S


def soulx_first_reply(rows: list[dict], margin: float, wait: int, direct: bool = True) -> dict | None:
    count = 0
    for r in rows:
        lg = r["logits"]
        if direct and r["direct_complete"] and r["speech_detected"]:
            return r
        if r["decision"]:
            if r["speech_detected"] and lg["complete"] - lg["incomplete"] > margin:
                return r
            count = 0
            continue
        if not r["monitoring"]:
            count = 0
            continue
        if r["argmax"] == "<|user_idle|>":
            count += 1
            if count >= wait and r["speech_detected"]:
                return r
        elif r["argmax"] == "<|user_backchannel|>":
            count = 1
        elif r["argmax"] == "<|user_incomplete|>":
            count = 0
    return None


def semvad_first_reply(d: dict, conf: float, imm: float, conf_ms: int, imm_ms: int, max_pause_ms: int) -> float | None:
    in_speech, silence, cand, ready = False, 0, None, 0.0
    for f, sp in enumerate(d["speech"]):
        if sp:
            in_speech, silence, cand = True, 0, None
            continue
        if not in_speech:
            continue
        silence += 1
        silence_ms = silence * FRAME_MS
        if cand is None and silence_ms >= CANDIDATE_MS:
            cand, compute = d["eou_at"][f]
            ready = on_packet((f + 1) * d["frame_s"]) + compute
        required = max_pause_ms
        if cand is not None and cand >= imm:
            required = max(CANDIDATE_MS, imm_ms)
        elif cand is not None and cand >= conf:
            required = max(CANDIDATE_MS, conf_ms)
        if silence_ms >= required:
            return max(on_packet((f + 1) * d["frame_s"]), ready)
    return None


def silence_first_reply(d: dict, silence_ms: int) -> float | None:
    in_speech, silence = False, 0
    for f, sp in enumerate(d["speech"]):
        if sp:
            in_speech, silence = True, 0
            continue
        if in_speech:
            silence += 1
            if silence * FRAME_MS >= silence_ms:
                return on_packet((f + 1) * d["frame_s"])
    return None


def commit_time(kind, params, soulx_rows, eou_d, lang) -> float | None:
    if kind == "soulx":
        r = soulx_first_reply(soulx_rows, *params)
        return None if r is None else r["ready"] + TERMINAL_ASR_S[lang]
    if kind == "semvad":
        return semvad_first_reply(eou_d, *params)
    return silence_first_reply(eou_d, *params)


def metrics(samples: list[Sample], commits: list[float | None], backend: float) -> dict:
    n = len(samples)
    if samples[0].task == "pause":
        hold = [c is not None and s.pause[0] <= c <= s.pause[1] + PAUSE_SLACK_S for s, c in zip(samples, commits)]
        return {"n": n, "takeover": sum(c is not None for c in commits) / n, "hold_violation": sum(hold) / n}
    delays = np.array([math.inf if c is None else c + backend - s.user_end for s, c in zip(samples, commits)])
    on_time = delays[(delays >= 0) & np.isfinite(delays)]
    out = {"n": n, "premature": float((delays < 0).mean()), "miss": float(np.isinf(delays).mean())}
    for d in DEADLINES_S:
        out[f"timely_{d:g}s"] = float(((delays >= 0) & (delays <= d)).mean())
    out["ontime_p50"] = float(np.percentile(on_time, 50)) if on_time.size else None
    out["ontime_p90"] = float(np.percentile(on_time, 90)) if on_time.size else None
    return out


def policies():
    for margin, wait in itertools.product([*np.arange(-6, 8.5, 0.5), math.inf], [1, 2, 3, 4, 5, 6, 8, 10, 12, 16]):
        yield "soulx", f"margin={margin:g},wait={wait}", ("soulx", (margin, wait, True))
        yield "soulx-eos", f"margin={margin:g},wait={wait}", ("soulx", (margin, wait, False))
    for name, cfg in SEMVAD_PRESETS.items():
        yield "semvad", f"preset={name}", ("semvad", cfg)
    for conf, conf_ms, max_ms in itertools.product([0.5, 0.6, 0.7, 0.8, 0.88, 0.95], [160, 320, 480, 640, 960],
                                                   [800, 1200, 2000, 3000]):
        if conf_ms <= max_ms:
            yield "semvad", f"conf={conf},conf_ms={conf_ms},max_ms={max_ms}", ("semvad", (conf, 1.01, conf_ms, conf_ms, max_ms))
    for ms in [160, 256, 320, 480, 640, 800, 1000, 1200, 1600, 2000]:
        yield "silence", f"silence_ms={ms}", ("silence", (ms,))


def average(per_draw: list[dict]) -> dict:
    out = {}
    for k, v in per_draw[0].items():
        vals = [d[k] for d in per_draw]
        out[k] = None if any(x is None for x in vals) else float(np.mean(vals))
    return out


def agreement(draws, by_subset) -> dict:
    """Share of samples whose default-policy first commitment falls on the same chunk in every draw."""
    out = {}
    for subset, ks in by_subset.items():
        same = 0
        for k in ks:
            firsts = {None if (r := soulx_first_reply(sx[k][1], 0.0, 8)) is None else round(r["t"], 3) for sx in draws}
            same += len(firsts) == 1
        out[subset] = same / len(ks)
    return out


REPLAY_DIR = {"candor_turn_taking": "turn-en", "synthetic_pause_handling": "pause-en", "turn_taking": "turn-zh",
              "pause_handling": "pause-zh"}


def calibrate(soulx, replay_out: Path) -> dict:
    """Committing chunk of the default SoulX policy vs. the first 'speak' chunk of a real replay of the same data."""
    per_subset = {}
    for (subset, sid), (_, rows) in soulx.items():
        t = replay_out / REPLAY_DIR.get(subset, "-") / sid / "timing.json"
        if not t.exists():
            continue
        st = per_subset.setdefault(subset, {"samples": 0, "same_chunk": 0, "both_silent": 0, "differ": []})
        st["samples"] += 1
        real = next((round(a, 3) for a, _, s in json.loads(t.read_text())["turn_chunk_log"] if s == "speak"), None)
        sim = soulx_first_reply(rows, 0.0, 8)
        sim = None if sim is None else round(sim["t"], 3)
        if real is None and sim is None:
            st["both_silent"] += 1
        elif real == sim:
            st["same_chunk"] += 1
        else:
            st["differ"].append([sid, sim, real])
    return per_subset


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--soulx", type=Path, nargs="+", required=True)
    ap.add_argument("--eou", type=Path, required=True)
    ap.add_argument("--data-counts", type=Path, required=True, help="JSON {subset: number of samples in the dataset}")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--calib", type=Path)
    args = ap.parse_args()
    draws, eou = [load_soulx(d) for d in args.soulx], load_eou(args.eou)
    expected = json.loads(args.data_counts.read_text())
    by_subset: dict[str, list[tuple[str, str]]] = {}
    for k in sorted(eou):
        by_subset.setdefault(k[0], []).append(k)
    coverage = {s: {"expected": n, "eou": len(by_subset.get(s, [])),
                    "soulx": [sum(k[0] == s for k in sx) for sx in draws]} for s, n in expected.items()}
    if any(c["eou"] != c["expected"] or any(x != c["expected"] for x in c["soulx"]) for c in coverage.values()):
        raise SystemExit(f"incomplete logs: {coverage}")
    args.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for family, name, (kind, params) in policies():
        for subset, ks in sorted(by_subset.items()):
            lang = SUBSET_LANG[subset]
            samples = [eou[k][0] for k in ks]
            per_draw = [metrics(samples, [commit_time(kind, params, sx[k][1], eou[k][1], lang) for k in ks], BACKEND_S[lang])
                        for sx in (draws if kind == "soulx" else draws[:1])]
            rows.append({"family": family, "policy": name, "subset": subset, "lang": lang, "draws": len(per_draw),
                         **average(per_draw)})
    fields = ["family", "policy", "subset", "lang", "draws", "n", "takeover", "hold_violation", "premature", "miss",
              *[f"timely_{d:g}s" for d in DEADLINES_S], "ontime_p50", "ontime_p90"]
    with open(args.out / "sweep.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    # note (luojiaxuan): SoulX resets instead of waiting on these rows, so first commitments after them are approximate.
    rows_all = [r for sx in draws for _, rs in sx.values() for r in rs]
    summary = {"coverage": coverage,
               "soulx_rows_reset_without_speech": sum((r["decision"] or r["direct_complete"]) and not r["speech_detected"] for r in rows_all),
               "soulx_direct_complete_rows": sum(r["direct_complete"] for r in rows_all),
               "soulx_mistake_decisions": sum(r["decision"] and r["argmax"] != "<|user_idle|>" for r in rows_all),
               "soulx_default_same_chunk_across_draws": agreement(draws, by_subset)}
    if args.calib:
        summary["calibration"] = [calibrate(sx, args.calib) for sx in draws]
    (args.out / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: v for k, v in summary.items() if k != "calibration"}))
    if args.calib:
        for cal in summary["calibration"]:
            print(json.dumps({s: {k: (len(v) if k == "differ" else v) for k, v in st.items()} for s, st in cal.items()}))


if __name__ == "__main__":
    main()
