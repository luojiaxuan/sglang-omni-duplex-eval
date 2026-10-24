# SPDX-License-Identifier: Apache-2.0
"""Causal replay of Full-Duplex-Bench samples through a cascaded turn detector -> LLM -> TTS stack.

Each sample's input.wav is streamed in 160 ms chunks at wall-clock pace. Response audio is
placed on an output timeline at max(arrival time, end of the previous chunk) and written as
output.wav (24 kHz) beside timing.json, so the official FDB scoring scripts run unchanged on
the output tree.

Modes:
  oracle  the response starts at the annotated user-turn end with a precomputed transcript
          (oracle_text.txt); measures the LLM + TTS critical path alone.
  turn    SoulX-Duplug servers decide the turn; no speculation.

Samples carry turn_taking.json (turn end = its first event start) or pause.json (pause handling;
the turn end is the end of the input, so every response is a takeover).
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import re
import shutil
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

import aiohttp
import numpy as np
import soundfile as sf
import soxr

IN_SR = 16000
OUT_SR = 24000
CHUNK_S = 0.16
CHUNK = int(IN_SR * CHUNK_S)

SYSTEM_PROMPT = {
    "en": (
        "You are a voice assistant talking with the user. Reply in a natural, brief, "
        "colloquial way, in English. No lists or markdown."
    ),
    "zh": "你是一个语音助手,正在和用户对话。请用自然、简短、口语化的中文回答,不要使用列表或 markdown。",
}
TTS_VOICE = {"en": ("Ryan", "English"), "zh": ("Vivian", "Chinese")}
CLAUSE_END = re.compile(r"[,，、;；:：.。!！?？\n]")
SENTENCE_END = re.compile(r"[.。!！?？\n]")


@dataclass
class Sample:
    sid: str
    src: Path
    audio: np.ndarray
    user_end: float
    oracle_text: str | None


@dataclass
class Response:
    decide_t: float
    text_in: str
    llm_first_token_t: float | None = None
    first_segment_t: float | None = None
    tts_first_pcm_t: float | None = None
    first_audio_t: float | None = None
    cut_at: float | None = None
    text_out: str = ""
    segments: list[dict] = field(default_factory=list)


def load_samples(root: Path, limit: int | None) -> list[Sample]:
    samples = []
    for d in sorted(p for p in root.iterdir() if (p / "input.wav").exists()):
        audio, sr = sf.read(d / "input.wav", dtype="float32", always_2d=True)
        audio = audio.mean(axis=1)
        if sr != IN_SR:
            audio = soxr.resample(audio, sr, IN_SR).astype(np.float32)
        if (d / "turn_taking.json").exists():
            user_end = float(json.loads((d / "turn_taking.json").read_text())[0]["timestamp"][0])
        else:
            user_end = len(audio) / IN_SR
        oracle = d / "oracle_text.txt"
        samples.append(
            Sample(
                sid=d.name,
                src=d,
                audio=audio,
                user_end=user_end,
                oracle_text=oracle.read_text().strip() if oracle.exists() else None,
            )
        )
    return samples[:limit] if limit else samples


class Timeline:
    def __init__(self, duration_s: float):
        self.buf = np.zeros(int(duration_s * OUT_SR), dtype=np.float32)
        self.cursor = 0.0

    def place(self, pcm: np.ndarray, arrival_t: float, cut_at: float | None) -> float:
        start = max(arrival_t, self.cursor)
        end = start + len(pcm) / OUT_SR
        stop = end if cut_at is None else min(end, cut_at)
        n = max(0, int((stop - start) * OUT_SR))
        i = int(start * OUT_SR)
        seg = pcm[:n][: max(0, len(self.buf) - i)]
        self.buf[i : i + len(seg)] += seg
        self.cursor = end
        return start


class Session:
    def __init__(self, args, http: aiohttp.ClientSession, sample: Sample, out_dir: Path, turn_url: str | None):
        self.args = args
        self.http = http
        self.s = sample
        self.out_dir = out_dir
        self.turn_url = turn_url
        self.timeline = Timeline(len(sample.audio) / IN_SR)
        self.responses: list[Response] = []
        self.chunk_log: list[tuple[float, float, str]] = []
        self.t0 = 0.0
        self.active: Response | None = None
        self.turn_session_id = f"{sample.sid}-{uuid.uuid4().hex[:8]}"

    def now(self) -> float:
        return time.perf_counter() - self.t0

    async def run(self):
        self.t0 = time.perf_counter()
        tasks = []
        if self.args.mode == "oracle":
            await asyncio.sleep(max(0.0, self.s.user_end - self.now()))
            tasks.append(asyncio.create_task(self.respond(self.s.oracle_text)))
            await asyncio.sleep(max(0.0, len(self.s.audio) / IN_SR - self.now()))
        else:
            async with self.http.ws_connect(self.turn_url, max_msg_size=0) as ws:
                for i in range(0, len(self.s.audio), CHUNK):
                    chunk_end = min(i + CHUNK, len(self.s.audio)) / IN_SR
                    await asyncio.sleep(max(0.0, chunk_end - self.now()))
                    payload = self.s.audio[i : i + CHUNK].astype(np.float32).tobytes()
                    await ws.send_str(
                        json.dumps(
                            {"type": "audio", "session_id": self.turn_session_id, "audio": base64.b64encode(payload).decode()}
                        )
                    )
                    msg = json.loads((await ws.receive()).data)
                    state = msg["state"]
                    st = state["state"]
                    self.chunk_log.append((chunk_end, self.now(), st))
                    if st == "nonidle" and self.active is not None and self.active.cut_at is None:
                        self.active.cut_at = self.now()
                    if st == "speak" and state.get("text", "").strip():
                        tasks.append(asyncio.create_task(self.respond(state["text"].strip())))
        await asyncio.gather(*tasks)
        self.dump()

    async def respond(self, text: str):
        r = Response(decide_t=self.now(), text_in=text)
        if self.active is not None and self.active.cut_at is None:
            self.active.cut_at = r.decide_t
        self.timeline.cursor = min(self.timeline.cursor, r.decide_t)
        self.responses.append(r)
        self.active = r
        lang = self.args.lang
        messages = [{"role": "system", "content": SYSTEM_PROMPT[lang]}]
        for prev in self.responses[:-1]:
            messages += [{"role": "user", "content": prev.text_in}, {"role": "assistant", "content": prev.text_out}]
        messages.append({"role": "user", "content": text})

        seg_q: asyncio.Queue[str | None] = asyncio.Queue()
        speaker = asyncio.create_task(self.speak(r, seg_q))
        body = {
            "model": self.args.llm_model,
            "messages": messages,
            "stream": True,
            "temperature": 0.0,
            "max_tokens": self.args.max_tokens,
        }
        buf, first_seg = "", True
        async with self.http.post(f"{self.args.llm_url}/v1/chat/completions", json=body) as resp:
            resp.raise_for_status()
            async for line in resp.content:
                line = line.decode().strip()
                if not line.startswith("data:") or line == "data: [DONE]":
                    continue
                delta = json.loads(line[5:])["choices"][0]["delta"].get("content") or ""
                if not delta:
                    continue
                if r.llm_first_token_t is None:
                    r.llm_first_token_t = self.now()
                r.text_out += delta
                buf += delta
                pattern = CLAUSE_END if first_seg else SENTENCE_END
                m = None
                for m in pattern.finditer(buf):
                    pass
                if m is not None and buf[: m.end()].strip():
                    if first_seg:
                        r.first_segment_t = self.now()
                        first_seg = False
                    await seg_q.put(buf[: m.end()])
                    buf = buf[m.end() :]
        if buf.strip():
            if first_seg:
                r.first_segment_t = self.now()
            await seg_q.put(buf)
        await seg_q.put(None)
        await speaker

    async def speak(self, r: Response, seg_q: asyncio.Queue):
        voice, language = TTS_VOICE[self.args.lang]
        while (seg := await seg_q.get()) is not None:
            seg_rec = {"text": seg, "request_t": self.now(), "first_pcm_t": None, "samples": 0}
            r.segments.append(seg_rec)
            body = {
                "model": self.args.tts_model,
                "input": seg,
                "voice": voice,
                "language": language,
                "stream": True,
                "response_format": "pcm",
            }
            pending = b""
            async with self.http.post(f"{self.args.tts_url}/v1/audio/speech", json=body) as resp:
                resp.raise_for_status()
                async for data in resp.content.iter_any():
                    t = self.now()
                    pending += data
                    usable = len(pending) - len(pending) % 2
                    if usable == 0:
                        continue
                    pcm = np.frombuffer(pending[:usable], dtype=np.int16).astype(np.float32) / 32768.0
                    pending = pending[usable:]
                    if seg_rec["first_pcm_t"] is None:
                        seg_rec["first_pcm_t"] = t
                    if r.tts_first_pcm_t is None:
                        r.tts_first_pcm_t = t
                    placed = self.timeline.place(pcm, t, r.cut_at)
                    if r.first_audio_t is None:
                        r.first_audio_t = placed
                    seg_rec["samples"] += len(pcm)

    def dump(self):
        d = self.out_dir / self.s.sid
        d.mkdir(parents=True, exist_ok=True)
        sf.write(d / "output.wav", self.timeline.buf, OUT_SR)
        for name in ("input.wav", "turn_taking.json", "pause.json"):
            if (self.s.src / name).exists():
                shutil.copy(self.s.src / name, d / name)
        lags = [wall - audio_t for audio_t, wall, _ in self.chunk_log]
        timing = {
            "sid": self.s.sid,
            "mode": self.args.mode,
            "user_end": self.s.user_end,
            "responses": [asdict(r) for r in self.responses],
            "turn_chunks": len(self.chunk_log),
            "turn_lag_p50": float(np.percentile(lags, 50)) if lags else None,
            "turn_lag_max": max(lags) if lags else None,
            "turn_chunk_log": self.chunk_log,
        }
        (d / "timing.json").write_text(json.dumps(timing, ensure_ascii=False, indent=1))


async def warmup(args, http: aiohttp.ClientSession):
    voice, language = TTS_VOICE[args.lang]
    text = {"en": "Sure, that sounds good to me.", "zh": "好的,我明白你的意思。"}[args.lang]
    tts_body = {"model": args.tts_model, "input": text, "voice": voice, "language": language,
                "stream": True, "response_format": "pcm"}
    llm_body = {"model": args.llm_model, "messages": [{"role": "user", "content": text}],
                "stream": True, "max_tokens": 16, "temperature": 0.0}

    async def drain(url, body):
        async with http.post(url, json=body) as resp:
            resp.raise_for_status()
            async for _ in resp.content.iter_any():
                pass

    for _ in range(args.warmup_rounds):
        await asyncio.gather(
            *(drain(f"{args.tts_url}/v1/audio/speech", tts_body) for _ in range(args.concurrency)),
            *(drain(f"{args.llm_url}/v1/chat/completions", llm_body) for _ in range(args.concurrency)),
        )


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--lang", choices=["en", "zh"], required=True)
    ap.add_argument("--mode", choices=["oracle", "turn"], required=True)
    ap.add_argument("--turn-urls", nargs="*", default=[])
    ap.add_argument("--llm-url", default="http://127.0.0.1:30000")
    ap.add_argument("--llm-model", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--tts-url", default="http://127.0.0.1:8000")
    ap.add_argument("--tts-model", default="Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice")
    ap.add_argument("--max-tokens", type=int, default=256)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--warmup-rounds", type=int, default=4)
    args = ap.parse_args()

    samples = load_samples(args.data, args.limit)
    if args.mode == "oracle":
        missing = [s.sid for s in samples if s.oracle_text is None]
        if missing:
            raise SystemExit(f"oracle_text.txt missing for {len(missing)} samples, e.g. {missing[:3]}")
    else:
        if not args.turn_urls:
            raise SystemExit("--turn-urls is required in turn mode")
    sem = asyncio.Semaphore(args.concurrency)
    free_urls: asyncio.Queue[str | None] = asyncio.Queue()
    for url in args.turn_urls or [None] * args.concurrency:
        free_urls.put_nowait(url)
    timeout = aiohttp.ClientTimeout(total=None, sock_read=120)

    async with aiohttp.ClientSession(timeout=timeout) as http:
        await warmup(args, http)

        async def one(sample: Sample):
            async with sem:
                if (args.out / sample.sid / "timing.json").exists():
                    return
                url = await free_urls.get()
                await Session(args, http, sample, args.out, url).run()
                free_urls.put_nowait(url)

        await asyncio.gather(*(one(s) for s in samples))


if __name__ == "__main__":
    asyncio.run(main())
