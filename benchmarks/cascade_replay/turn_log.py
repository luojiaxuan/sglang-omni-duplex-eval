# SPDX-License-Identifier: Apache-2.0
"""Log SoulX-Duplug's per-chunk state logits on FDB samples, for offline threshold sweeps.

SoulX decides a reply at the first idle chunk after speech: it replies if the <|user_complete|>
logit beats <|user_incomplete|>, otherwise it waits and replies after max_wait_num idle chunks.
This logger runs the same model but always takes the wait branch and never replies (an argmax
<|user_complete|> elsewhere, which SoulX answers regardless of these rules, is logged and waited out). Every policy
that only changes those two rules (a logit margin, a wait length) sees exactly this trajectory up
to its first reply, so sweep.py can find each policy's first reply from one logged pass.

Run from a SoulX-Duplug checkout (config paths are relative), with its venv:
  python turn_log.py --data <subset>... --out <dir> --shard 0/4
Writes <out>/<subset>/<sample>.jsonl, one line per 160 ms chunk.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import zlib
from pathlib import Path

import numpy as np
import soundfile as sf
import soxr
import torch

sys.path.insert(0, str(Path.cwd()))
from service.model import TurnModel  # noqa: E402

from fdb_meta import sample_meta  # noqa: E402

SR = 16000
CHUNK = 2560
STATES = ("idle", "nonidle", "backchannel", "complete", "incomplete")


class LoggingTurnModel(TurnModel):
    def _init_hyperparameters(self):
        super()._init_hyperparameters()
        self.config.infer_config["max_wait_num"] = 10**9
        self.state_ids = {s: self.model.tokenizer.convert_tokens_to_ids(f"<|user_{s}|>") for s in STATES}
        self.last = None

    def _state_predict(self, delta_text):
        with torch.no_grad():
            outputs = self.model.llm(
                inputs_embeds=self.past_state["input_embeds"],
                past_key_values=self.past_state["past_key_values"],
                use_cache=True,
            )
        logits = outputs.logits[0, -1].float()
        pred = torch.argmax(logits)
        state = self.model.tokenizer.decode(pred)
        if state == "<|user_nonidle|>" and not delta_text:
            self.past_state["mistake_len"] += 1
        else:
            self.past_state["mistake_len"] = 0
        decision = (
            self.past_state["state"] == "<|user_nonidle|>" and state == "<|user_idle|>"
        ) or self.past_state["mistake_len"] >= self.config.infer_config.max_mistake_num
        # note (luojiaxuan): an argmax <|user_complete|> outside the end-of-speech decision replies under every
        # policy; it is logged as such and the logger keeps waiting so the trajectory stays reply-free.
        direct_complete = not decision and state == "<|user_complete|>"
        self.last = {
            "argmax": state,
            "logits": {s: round(logits[i].item(), 4) for s, i in self.state_ids.items()},
            "decision": bool(decision),
            "direct_complete": direct_complete,
        }
        if decision or direct_complete:
            state = "<|user_incomplete|>"
            self.past_state["input_embeds"] = self.action_wait_embeds
        else:
            self.past_state["input_embeds"] = self.embed_tokens_func(pred.unsqueeze(0))
        self.past_state["past_key_values"] = outputs.past_key_values
        self.past_state["state"] = state
        return state


def run_sample(model: LoggingTurnModel, wav: Path, out: Path, seed: int):
    audio, sr = sf.read(wav, dtype="float32", always_2d=True)
    audio = audio.mean(axis=1)
    if sr != SR:
        audio = soxr.resample(audio, sr, SR).astype(np.float32)
    # note (luojiaxuan): reset() fills SoulX's buffers with random noise that changes its decisions on near-silent
    # chunks; a per-sample seed makes a log reproducible regardless of sharding and order.
    np.random.seed((seed * 1_000_003 + zlib.crc32(f"{wav.parent.parent.name}/{wav.parent.name}".encode())) % 2**32)
    model.reset()
    rows = [{"meta": {**sample_meta(wav.parent, len(audio) / SR), "seed": seed}}]
    for i in range(0, len(audio), CHUNK):
        model.last = None
        t = time.perf_counter()
        res = model.process(audio[i : i + CHUNK])
        compute = time.perf_counter() - t
        row = {"t": round(min(i + CHUNK, len(audio)) / SR, 3), "compute": round(compute, 4), "out": res["state"],
               "speech_detected": bool(model.speech_detected), "monitoring": bool(model.monitoring_wait_silence)}
        if model.last is not None:
            row.update(model.last)
        rows.append(row)
    tmp = out.with_suffix(".tmp")
    tmp.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    tmp.rename(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, nargs="+", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--seed", type=int, required=True)
    args = ap.parse_args()
    k, n = map(int, args.shard.split("/"))
    jobs = []
    for subset in args.data:
        for d in sorted(p for p in subset.iterdir() if (p / "input.wav").exists()):
            jobs.append((subset.name, d))
    model = LoggingTurnModel(config_path="config/config.yaml")
    for j, (subset, d) in enumerate(jobs):
        if j % n != k:
            continue
        out = args.out / subset / f"{d.name}.jsonl"
        if out.exists():
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        run_sample(model, d / "input.wav", out, args.seed)
    print(f"TURN_LOG_DONE shard {k}/{n}")


if __name__ == "__main__":
    main()
