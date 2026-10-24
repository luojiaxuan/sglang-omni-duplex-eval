#!/usr/bin/env python3
"""Per-session turn-detection metrics for legacy-protocol (half-duplex) FDB recordings.

Inputs
  --rec  rec/<arm>        recorder run dir: run.json, manifest.json,
                          samples/<subset>/<id>/input/continuous.jsonl
  --ref  score/<arm>/ref  exporter tree: <subset>/<id>/{output.json, pause.json |
                          turn_taking.json}, manifest.json
  --out  out/<arm>        sessions.jsonl, sessions.csv, summary.json

Clock: every time is seconds relative to t0 = client send start of the first
input_audio_buffer.append (the exporter's origin). Input end T = t0 + unpadded
input duration. Playout accounting mirrors reference_audio.analyze_variant:
FIFO zero-buffer receipt-time playout at the native 24 kHz rate, cursor cut at
input_audio_buffer.speech_started / output_audio_buffer.cleared, deltas received
after T excluded, buffer cropped at T.
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import statistics
from pathlib import Path

INPUT_RATE = 16000
APPEND = "input_audio_buffer.append"
SPEECH_STARTED = "input_audio_buffer.speech_started"
SPEECH_STOPPED = "input_audio_buffer.speech_stopped"
COMMITTED = "input_audio_buffer.committed"
RESPONSE_CREATED = "response.created"
RESPONSE_DONE = "response.done"
AUDIO_DELTA = "response.audio.delta"
AUDIO_DONE = "response.audio.done"
TEXT_DELTA = "response.text.delta"
TEXT_DONE = "response.text.done"
CLEARED = "output_audio_buffer.cleared"
INPUT_TRANSCRIPT_DONE = "conversation.item.input_audio_transcription.completed"
# note (luojiaxuan): A response.created this close after a commit answers that
# commit; later ones answer a queued, previously unanswered commit.
IMMEDIATE_RESPONSE_S = 0.05
# note (luojiaxuan): official eval_pause_handling / eval_smooth_turn_taking rule.
TOR_DURATION_S = 1.0
TOR_MAX_WORDS = 3
TEXT_EXCERPT = 300


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def describe(values: list[float]) -> dict:
    clean = [v for v in values if v is not None]
    return {
        "n": len(clean),
        "mean": statistics.fmean(clean) if clean else None,
        "median": percentile(clean, 0.5),
        "p90": percentile(clean, 0.9),
        "min": min(clean) if clean else None,
        "max": max(clean) if clean else None,
    }


def overlap(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def load_annotation(ref_sample: Path, task: str) -> list[tuple[float, float]]:
    name = "pause.json" if task == "pause_handling" else "turn_taking.json"
    rows = json.loads((ref_sample / name).read_text())
    return [(float(r["timestamp"][0]), float(r["timestamp"][1])) for r in rows]


def official_tor(chunks: list[dict]) -> tuple[int, float | None, int]:
    """(TOR, transcript span s, words) by the official rule."""
    if not chunks:
        return 0, None, 0
    first = chunks[0]["timestamp"][0]
    last_end = chunks[-1]["timestamp"][1]
    span = (chunks[-1]["timestamp"][0] if last_end is None else last_end) - first
    if span < TOR_DURATION_S and len(chunks) <= TOR_MAX_WORDS:
        return 0, span, len(chunks)
    return 1, span, len(chunks)


def analyze_session(
    trace_path: Path,
    task: str,
    annotation: list[tuple[float, float]],
    output_json: dict,
    output_rate: int,
    pause_allowance_s: float | None,
) -> dict:
    rows = [json.loads(line) for line in trace_path.open(encoding="utf-8")]
    t0 = next(
        r["time_s"]
        for r in rows
        if r["direction"] == "send" and r["event"]["type"] == APPEND
    )
    last_append = [
        r["event"] for r in rows if r["direction"] == "send" and r["event"]["type"] == APPEND
    ][-1]
    input_end_s = last_append["sglang"]["t_start_ms"] / 1000 + len(
        base64.b64decode(last_append["audio"], validate=True)
    ) / (2 * INPUT_RATE)
    configure = next(
        r["event"]["session"]
        for r in rows
        if r["direction"] == "send" and r["event"]["type"] == "session.update"
    )
    turn_detection = configure["turn_detection"]
    interrupts_on_speech = turn_detection.get("interrupt_response") is not False
    silence_s = (
        turn_detection.get("silence_duration_ms", 0) / 1000
        if pause_allowance_s is None
        else pause_allowance_s
    )
    session = {
        "t0_abs_s": t0,
        "input_end_s": input_end_s,
        "turn_detection": turn_detection,
        "session_created_s": None,
        "session_updated_s": None,
        "probe_sent_s": None,
        "probe_ack_s": None,
        "last_event_s": None,
        "client_errors": [],
    }
    speech_starts: list[dict] = []
    commits: list[dict] = []
    responses: list[dict] = []
    by_id: dict[str, dict] = {}
    cuts: list[dict] = []
    stops_pending: list[dict] = []
    input_transcripts: list[str] = []
    cursor = 0
    segments: list[dict] = []  # FIFO playout timeline, one per response
    open_speech = None
    first_updated = True

    def active_response() -> dict | None:
        for response in reversed(responses):
            if response["done_s"] is None:
                return response
        return None

    def apply_cut(kind: str, at_s: float) -> None:
        nonlocal cursor
        cut = round(at_s * output_rate)
        dropped = cursor - cut
        if dropped <= 0:
            return
        affected = []
        for segment in segments:
            if segment["end"] > cut:
                new_end = max(segment["start"], cut)
                lost = segment["end"] - new_end
                segment["end"] = new_end
                response = by_id[segment["response_id"]]
                response["audio_s_cut_by_barge_in"] += lost / output_rate
                response["cut_by"] = response["cut_by"] or kind
                response["cut_s"] = response["cut_s"] if response["cut_s"] is not None else at_s
                affected.append(segment["response_id"])
        cursor = cut
        cuts.append(
            {
                "type": kind,
                "time_s": at_s,
                "dropped_s": dropped / output_rate,
                "responses": affected,
            }
        )

    for row in rows:
        event = row["event"]
        kind = event.get("type")
        at = row["time_s"] - t0
        direction = row["direction"]
        if direction == "send":
            if kind == "session.update" and session["session_updated_s"] is not None:
                session["probe_sent_s"] = at
            continue
        if direction == "error":
            session["client_errors"].append({"time_s": at, "message": event["message"]})
            continue
        if direction != "receive":
            continue
        session["last_event_s"] = at
        if kind == "session.created":
            session["session_created_s"] = at
        elif kind == "session.updated":
            if first_updated:
                session["session_updated_s"] = at
                first_updated = False
            else:
                session["probe_ack_s"] = at
        elif kind == SPEECH_STARTED:
            open_speech = {
                "time_s": at,
                "audio_start_s": event["audio_start_ms"] / 1000,
                "item_id": event["item_id"],
                "stopped_s": None,
                "after_input_end": at > input_end_s,
                "interrupted_response": None,
            }
            active = active_response()
            if active is not None:
                open_speech["interrupted_response"] = active["id"]
                active["interrupted_by_speech_s"] = at
            speech_starts.append(open_speech)
            if interrupts_on_speech:
                apply_cut(SPEECH_STARTED, at)
        elif kind == SPEECH_STOPPED:
            stop = {
                "time_s": at,
                "audio_end_s": event["audio_end_ms"] / 1000,
                "item_id": event["item_id"],
            }
            if open_speech is not None and open_speech["item_id"] == event["item_id"]:
                open_speech["stopped_s"] = at
            open_speech = None
            stops_pending.append(stop)
        elif kind == COMMITTED:
            stop = next(
                (s for s in stops_pending if s["item_id"] == event["item_id"]), None
            )
            stops_pending = [s for s in stops_pending if s is not stop]
            commit = {
                "index": len(commits),
                "item_id": event["item_id"],
                "time_s": at,
                "speech_stopped_s": stop["time_s"] if stop else None,
                "speech_end_s": stop["audio_end_s"] if stop else None,
                "speech_end_to_commit_s": (at - stop["audio_end_s"]) if stop else None,
                "before_input_end": at < input_end_s,
                "speech_end_before_input_end": (
                    stop["audio_end_s"] < input_end_s if stop else None
                ),
                "before_last_word_start": (
                    at < annotation[0][0] if task == "turn_taking" else None
                ),
                "before_last_word_end": (
                    at < annotation[0][1] if task == "turn_taking" else None
                ),
                "pause_index_by_commit_time": None,
                "pause_index_by_speech_end": None,
                "offset_from_pause_start_s": None,
                "response_id": None,
                "response_deferred": None,
                "swallowed_by_speech_started_s": None,
                "input_transcript": None,
            }
            if task == "pause_handling":
                for index, (start, end) in enumerate(annotation):
                    if start <= at <= end + silence_s and commit["pause_index_by_commit_time"] is None:
                        commit["pause_index_by_commit_time"] = index
                        commit["offset_from_pause_start_s"] = at - start
                    if stop and start <= stop["audio_end_s"] <= end and commit["pause_index_by_speech_end"] is None:
                        commit["pause_index_by_speech_end"] = index
            commits.append(commit)
        elif kind == RESPONSE_CREATED:
            response_id = event["response"]["id"]
            unanswered = [c for c in commits if c["response_id"] is None]
            immediate = (
                unanswered[-1]
                if unanswered and at - unanswered[-1]["time_s"] <= IMMEDIATE_RESPONSE_S
                else None
            )
            trigger = immediate if immediate is not None else (unanswered[0] if unanswered else None)
            response = {
                "id": response_id,
                "created_s": at,
                "trigger_commit_index": trigger["index"] if trigger else None,
                "trigger_commit_s": trigger["time_s"] if trigger else None,
                "deferred": trigger is not None and immediate is None,
                "commit_to_created_s": (at - trigger["time_s"]) if immediate else None,
                "first_text_s": None,
                "commit_to_first_text_s": None,
                "first_audio_s": None,
                "commit_to_first_audio_s": None,
                "created_to_first_audio_s": None,
                "last_audio_s": None,
                "audio_deltas": 0,
                "audio_s_received": 0.0,
                "audio_s_received_before_cut": 0.0,
                "audio_s_received_after_input_end": 0.0,
                "audio_s_cut_by_barge_in": 0.0,
                "audio_s_cropped_at_input_end": 0.0,
                "audio_s_survived": 0.0,
                "survived_window_s": None,
                "cut_by": None,
                "cut_s": None,
                "interrupted_by_speech_s": None,
                "done_s": None,
                "status": None,
                "status_reason": None,
                "created_to_done_s": None,
                "first_audio_to_done_s": None,
                "text": None,
                "text_chars": 0,
            }
            if trigger is not None:
                trigger["response_id"] = response_id
                trigger["response_deferred"] = response["deferred"]
            responses.append(response)
            by_id[response_id] = response
        elif kind == TEXT_DELTA:
            response = by_id[event["response_id"]]
            if response["first_text_s"] is None:
                response["first_text_s"] = at
                if response["commit_to_created_s"] is not None:
                    response["commit_to_first_text_s"] = at - response["trigger_commit_s"]
        elif kind == TEXT_DONE:
            response = by_id[event["response_id"]]
            response["text"] = event["text"][:TEXT_EXCERPT]
            response["text_chars"] = len(event["text"])
        elif kind == AUDIO_DELTA:
            response = by_id[event["response_id"]]
            samples = len(base64.b64decode(event["delta"], validate=True)) // 2
            seconds = samples / output_rate
            response["audio_deltas"] += 1
            response["audio_s_received"] += seconds
            response["last_audio_s"] = at
            if response["first_audio_s"] is None:
                response["first_audio_s"] = at
                response["created_to_first_audio_s"] = at - response["created_s"]
                if response["commit_to_created_s"] is not None:
                    response["commit_to_first_audio_s"] = at - response["trigger_commit_s"]
            if response["cut_s"] is None and response["interrupted_by_speech_s"] is None:
                response["audio_s_received_before_cut"] += seconds
            if at > input_end_s:
                response["audio_s_received_after_input_end"] += seconds
                continue
            start = max(cursor, round(at * output_rate))
            cursor = start + samples
            if segments and segments[-1]["response_id"] == event["response_id"] and segments[-1]["end"] == start:
                segments[-1]["end"] = cursor
            else:
                segments.append({"response_id": event["response_id"], "start": start, "end": cursor})
        elif kind == CLEARED:
            apply_cut(CLEARED, at)
        elif kind == RESPONSE_DONE:
            response = by_id[event["response"]["id"]]
            response["done_s"] = at
            response["status"] = event["response"]["status"]
            response["status_reason"] = event["response"]["status_details"]["reason"]
            response["created_to_done_s"] = at - response["created_s"]
            if response["first_audio_s"] is not None:
                response["first_audio_to_done_s"] = at - response["first_audio_s"]
        elif kind == INPUT_TRANSCRIPT_DONE:
            input_transcripts.append(event["transcript"])
            commit = next((c for c in commits if c["item_id"] == event["item_id"]), None)
            if commit is not None:
                commit["input_transcript"] = event["transcript"]

    for commit in commits:
        if commit["response_id"] is None:
            resumed = next(
                (s for s in speech_starts if s["time_s"] >= commit["time_s"]), None
            )
            commit["swallowed_by_speech_started_s"] = resumed["time_s"] if resumed else None

    # note (luojiaxuan): analyze_variant crops at the float window_s * rate.
    crop_at = input_end_s * output_rate
    for segment in segments:
        if segment["end"] > crop_at:
            lost = segment["end"] - max(segment["start"], crop_at)
            by_id[segment["response_id"]]["audio_s_cropped_at_input_end"] += lost / output_rate
            segment["end"] = max(segment["start"], crop_at)
    for response in responses:
        kept = [s for s in segments if s["response_id"] == response["id"] and s["end"] > s["start"]]
        response["audio_s_survived"] = sum(s["end"] - s["start"] for s in kept) / output_rate
        if kept:
            response["survived_window_s"] = [
                kept[0]["start"] / output_rate,
                kept[-1]["end"] / output_rate,
            ]

    chunks = output_json["chunks"]
    tor, span, words = official_tor(chunks)
    official = {
        "tor": tor,
        "transcript_words": words,
        "transcript_span_s": span,
        "first_word_start_s": chunks[0]["timestamp"][0] if chunks else None,
        "text": output_json["text"][:TEXT_EXCERPT],
    }
    if task == "pause_handling":
        in_pause = 0.0
        starts_in_pause = 0
        for chunk in chunks:
            start, end = chunk["timestamp"]
            end = start if end is None else end
            in_pause += sum(overlap(start, end, p0, p1) for p0, p1 in annotation)
            starts_in_pause += any(p0 <= start <= p1 for p0, p1 in annotation)
        official["transcribed_speech_in_pause_s"] = in_pause
        official["words_starting_in_pause"] = starts_in_pause
        official["any_word_starts_in_pause"] = starts_in_pause > 0
    else:
        last_word_start, last_word_end = annotation[0]
        latency = (official["first_word_start_s"] - last_word_start) if tor else None
        official["latency_s"] = None if latency is None else max(0.0, latency)
        official["latency_raw_s"] = latency
        official["first_word_before_final_commit"] = (
            chunks[0]["timestamp"][0] < commits[-1]["time_s"] if chunks and commits else None
        )

    audio_responses = [r for r in responses if r["first_audio_s"] is not None]
    summary = {
        "commits": len(commits),
        "false_endpoints": sum(c["before_input_end"] for c in commits),
        "commits_in_pause_by_commit_time": sum(
            c["pause_index_by_commit_time"] is not None for c in commits
        ),
        "commits_in_pause_by_speech_end": sum(
            c["pause_index_by_speech_end"] is not None for c in commits
        ),
        "commits_swallowed": sum(c["response_id"] is None for c in commits),
        "speech_starts": len(speech_starts),
        "speech_starts_after_input_end": sum(s["after_input_end"] for s in speech_starts),
        "speech_open_at_end": open_speech is not None,
        "responses": len(responses),
        "responses_deferred": sum(r["deferred"] for r in responses),
        "responses_with_audio": len(audio_responses),
        "responses_cancelled": sum(r["status"] == "cancelled" for r in responses),
        "responses_completed": sum(r["status"] == "completed" for r in responses),
        "responses_open_at_end": sum(r["done_s"] is None for r in responses),
        "responses_cut": sum(r["cut_by"] is not None for r in responses),
        "any_audio": bool(audio_responses),
        "any_audio_in_window": any(r["first_audio_s"] <= input_end_s for r in audio_responses),
        "first_audio_s": min((r["first_audio_s"] for r in audio_responses), default=None),
        "audio_s_received": sum(r["audio_s_received"] for r in responses),
        "audio_s_cut_by_barge_in": sum(r["audio_s_cut_by_barge_in"] for r in responses),
        "audio_s_cropped_at_input_end": sum(r["audio_s_cropped_at_input_end"] for r in responses),
        "audio_s_received_after_input_end": sum(
            r["audio_s_received_after_input_end"] for r in responses
        ),
        "audio_s_survived": sum(r["audio_s_survived"] for r in responses),
        "barge_in_cuts": len(cuts),
    }
    if task == "turn_taking":
        last_word_start, last_word_end = annotation[0]
        final = commits[-1] if commits else None
        final_response = (
            by_id[final["response_id"]]
            if final is not None and final["response_id"] is not None
            else None
        )
        summary["turn_taking"] = {
            "last_word_start_s": last_word_start,
            "last_word_end_s": last_word_end,
            "final_commit_s": final["time_s"] if final else None,
            "final_commit_minus_input_end_s": (final["time_s"] - input_end_s) if final else None,
            "final_commit_minus_last_word_end_s": (final["time_s"] - last_word_end) if final else None,
            "final_commit_minus_last_word_start_s": (
                final["time_s"] - last_word_start
            ) if final else None,
            "final_commit_speech_end_minus_last_word_end_s": (
                final["speech_end_s"] - last_word_end
            ) if final and final["speech_end_s"] is not None else None,
            "final_response_id": final_response["id"] if final_response else None,
            "final_response_first_audio_s": (
                final_response["first_audio_s"] if final_response else None
            ),
            "final_response_first_audio_minus_input_end_s": (
                final_response["first_audio_s"] - input_end_s
                if final_response and final_response["first_audio_s"] is not None
                else None
            ),
            "final_response_first_audio_minus_last_word_start_s": (
                final_response["first_audio_s"] - last_word_start
                if final_response and final_response["first_audio_s"] is not None
                else None
            ),
            "any_first_audio_minus_input_end_s": (
                summary["first_audio_s"] - input_end_s
                if summary["first_audio_s"] is not None
                else None
            ),
        }
    return {
        **session,
        "annotation": annotation,
        "input_transcripts": input_transcripts,
        "summary": summary,
        "official": official,
        "speech_starts": speech_starts,
        "commits": commits,
        "responses": responses,
        "cuts": cuts,
    }


def summarize(sessions: list[dict], task: str) -> dict:
    sess = [s for s in sessions if s["task"] == task]
    commits = [c for s in sess for c in s["commits"]]
    responses = [r for s in sess for r in s["responses"]]
    audio_responses = [r for r in responses if r["first_audio_s"] is not None]
    n = len(sess)

    def rate(count: int, denominator: int) -> dict:
        return {"count": count, "of": denominator, "rate": (count / denominator) if denominator else None}

    out = {
        "sessions": n,
        "sessions_any_audio": rate(sum(s["summary"]["any_audio"] for s in sess), n),
        "sessions_any_audio_in_window": rate(sum(s["summary"]["any_audio_in_window"] for s in sess), n),
        "sessions_survived_audio_gt0": rate(sum(s["summary"]["audio_s_survived"] > 0 for s in sess), n),
        "sessions_official_tor": rate(sum(s["official"]["tor"] for s in sess), n),
        "sessions_with_commit": rate(sum(s["summary"]["commits"] > 0 for s in sess), n),
        "sessions_with_false_endpoint": rate(sum(s["summary"]["false_endpoints"] > 0 for s in sess), n),
        "sessions_speech_open_at_end": rate(sum(s["summary"]["speech_open_at_end"] for s in sess), n),
        "sessions_with_client_error": rate(sum(bool(s["client_errors"]) for s in sess), n),
        "commits": len(commits),
        "commits_per_session": describe([s["summary"]["commits"] for s in sess]),
        "false_endpoints": rate(sum(c["before_input_end"] for c in commits), len(commits)),
        "commits_swallowed": rate(sum(c["response_id"] is None for c in commits), len(commits)),
        "commits_answered_immediately": rate(
            sum(c["response_id"] is not None and not c["response_deferred"] for c in commits), len(commits)
        ),
        "commits_answered_deferred": rate(
            sum(c["response_id"] is not None and c["response_deferred"] for c in commits), len(commits)
        ),
        "speech_end_to_commit_s": describe([c["speech_end_to_commit_s"] for c in commits]),
        "speech_starts": sum(s["summary"]["speech_starts"] for s in sess),
        "speech_starts_after_input_end": sum(s["summary"]["speech_starts_after_input_end"] for s in sess),
        "responses": len(responses),
        "responses_deferred": rate(sum(r["deferred"] for r in responses), len(responses)),
        "responses_with_audio": rate(len(audio_responses), len(responses)),
        "responses_cancelled": rate(sum(r["status"] == "cancelled" for r in responses), len(responses)),
        "responses_completed": rate(sum(r["status"] == "completed" for r in responses), len(responses)),
        "responses_open_at_end": rate(sum(r["done_s"] is None for r in responses), len(responses)),
        "responses_cut_by_exporter": rate(sum(r["cut_by"] is not None for r in responses), len(responses)),
        "responses_with_audio_cut": rate(
            sum(r["cut_by"] is not None for r in audio_responses), len(audio_responses)
        ),
        "responses_with_audio_fully_cut": rate(
            sum(r["audio_s_survived"] == 0 for r in audio_responses), len(audio_responses)
        ),
        "commit_to_created_s": describe([r["commit_to_created_s"] for r in responses]),
        "commit_to_first_text_s": describe([r["commit_to_first_text_s"] for r in responses]),
        "commit_to_first_audio_s": describe([r["commit_to_first_audio_s"] for r in responses]),
        "created_to_first_audio_s": describe([r["created_to_first_audio_s"] for r in responses]),
        "created_to_done_s": describe([r["created_to_done_s"] for r in responses]),
        "first_audio_to_done_s": describe([r["first_audio_to_done_s"] for r in responses]),
        "first_audio_to_cut_s": describe(
            [r["cut_s"] - r["first_audio_s"] for r in audio_responses if r["cut_s"] is not None]
        ),
        "audio_s_received_per_response": describe([r["audio_s_received"] for r in audio_responses]),
        "audio_s_received_before_cut_per_cut_response": describe(
            [r["audio_s_received_before_cut"] for r in audio_responses if r["cut_by"] is not None]
        ),
        "audio_s_survived_per_response": describe([r["audio_s_survived"] for r in audio_responses]),
        "audio_totals_s": {
            "received": sum(s["summary"]["audio_s_received"] for s in sess),
            "cut_by_barge_in": sum(s["summary"]["audio_s_cut_by_barge_in"] for s in sess),
            "cropped_at_input_end": sum(s["summary"]["audio_s_cropped_at_input_end"] for s in sess),
            "received_after_input_end": sum(s["summary"]["audio_s_received_after_input_end"] for s in sess),
            "survived": sum(s["summary"]["audio_s_survived"] for s in sess),
        },
        "official_transcript_words": describe([s["official"]["transcript_words"] for s in sess]),
    }
    if task == "pause_handling":
        pauses = [p for s in sess for p in s["annotation"]]
        durations = [p1 - p0 for p0, p1 in pauses]
        out["pauses"] = {"count": len(pauses), "duration_s": describe(durations)}
        out["commits_in_pause_by_commit_time"] = rate(
            sum(c["pause_index_by_commit_time"] is not None for c in commits), len(commits)
        )
        out["commits_in_pause_by_speech_end"] = rate(
            sum(c["pause_index_by_speech_end"] is not None for c in commits), len(commits)
        )
        out["pauses_with_commit_by_commit_time"] = rate(
            sum(
                1
                for s in sess
                for index in range(len(s["annotation"]))
                if any(c["pause_index_by_commit_time"] == index for c in s["commits"])
            ),
            len(pauses),
        )
        out["sessions_with_commit_in_pause"] = rate(
            sum(s["summary"]["commits_in_pause_by_commit_time"] > 0 for s in sess), n
        )
        out["offset_from_pause_start_s"] = describe([c["offset_from_pause_start_s"] for c in commits])
        out["sessions_any_word_starts_in_pause"] = rate(
            sum(s["official"]["any_word_starts_in_pause"] for s in sess), n
        )
        out["transcribed_speech_in_pause_s_total"] = sum(
            s["official"]["transcribed_speech_in_pause_s"] for s in sess
        )
        out["transcribed_speech_in_pause_s_per_session"] = describe(
            [s["official"]["transcribed_speech_in_pause_s"] for s in sess]
        )
        out["sessions_any_transcribed_word"] = rate(
            sum(s["official"]["transcript_words"] > 0 for s in sess), n
        )
    else:
        tt = [s["summary"]["turn_taking"] for s in sess]
        latencies = [s["official"]["latency_s"] for s in sess if s["official"]["latency_s"] is not None]
        out["official_latency_s"] = describe(latencies)
        out["official_latency_mean_s"] = statistics.fmean(latencies) if latencies else None
        for key in (
            "final_commit_minus_input_end_s",
            "final_commit_minus_last_word_end_s",
            "final_commit_minus_last_word_start_s",
            "final_commit_speech_end_minus_last_word_end_s",
            "final_response_first_audio_minus_input_end_s",
            "final_response_first_audio_minus_last_word_start_s",
            "any_first_audio_minus_input_end_s",
        ):
            out[key] = describe([t[key] for t in tt])
        out["sessions_final_commit_after_input_end"] = rate(
            sum(t["final_commit_s"] is not None and t["final_commit_s"] >= s["input_end_s"] for t, s in zip(tt, sess)), n
        )
        out["sessions_final_response_has_audio"] = rate(
            sum(t["final_response_first_audio_s"] is not None for t in tt), n
        )
        out["premature_commits_before_last_word_start"] = rate(
            sum(bool(c["before_last_word_start"]) for c in commits), len(commits)
        )
        out["sessions_with_premature_commit"] = rate(
            sum(any(c["before_last_word_start"] for c in s["commits"]) for s in sess), n
        )
        out["official_latency_negative_clipped"] = rate(
            sum(
                s["official"]["latency_raw_s"] is not None and s["official"]["latency_raw_s"] < 0
                for s in sess
            ),
            len(latencies),
        )
        out["sessions_first_word_before_final_commit"] = rate(
            sum(bool(s["official"]["first_word_before_final_commit"]) for s in sess), n
        )
        single = [
            s["official"]["latency_s"]
            for s in sess
            if s["summary"]["commits"] == 1 and s["official"]["latency_s"] is not None
        ]
        out["official_latency_single_commit_sessions_s"] = describe(single)
        clean = [
            s["official"]["latency_s"]
            for s in sess
            if not s["official"]["first_word_before_final_commit"]
            and s["official"]["latency_s"] is not None
        ]
        out["official_latency_first_word_after_final_commit_s"] = describe(clean)
    return out


def flat_row(session: dict) -> dict:
    row = {
        "sample_id": session["sample_id"],
        "task": session["task"],
        "input_end_s": round(session["input_end_s"], 3),
    }
    for key, value in session["summary"].items():
        if key == "turn_taking":
            for sub_key, sub_value in value.items():
                row[f"tt_{sub_key}"] = sub_value
        else:
            row[key] = value
    for key, value in session["official"].items():
        if key != "text":
            row[f"official_{key}"] = value
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rec", type=Path, required=True)
    parser.add_argument("--ref", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--output-rate", type=int, default=24000)
    parser.add_argument(
        "--pause-allowance-s",
        type=float,
        default=None,
        help="seconds after an annotated pause end within which a commit still counts as "
        "inside that pause; default is the arm's turn_detection.silence_duration_ms "
        "(0 when absent, e.g. semantic_vad)",
    )
    args = parser.parse_args()

    run = json.loads((args.rec / "run.json").read_text())
    arm_manifest = json.loads((args.rec / "manifest.json").read_text())
    sessions = []
    skipped = []
    for entry in sorted(run["samples"], key=lambda e: e["id"]):
        state = entry["variants"]["input"]
        if state["status"] != "pass" or state["protocol_verdict"] != "pass":
            skipped.append({"sample_id": entry["id"], "status": state["status"], "protocol_verdict": state["protocol_verdict"]})
            continue
        ref_sample = args.ref / entry["id"]
        trace_path = args.rec / state["directory"] / "continuous.jsonl"
        annotation = load_annotation(ref_sample, entry["task"])
        output_json = json.loads((ref_sample / "output.json").read_text())
        result = analyze_session(
            trace_path,
            entry["task"],
            annotation,
            output_json,
            args.output_rate,
            args.pause_allowance_s,
        )
        sessions.append(
            {
                "sample_id": entry["id"],
                "subset": entry["subset"],
                "task": entry["task"],
                "recorder": {
                    "media_duration_s": state["output"]["media_duration_s"],
                    "initial_delay_s": state["output"]["initial_delay_s"],
                },
                **result,
            }
        )

    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "sessions.jsonl").open("w", encoding="utf-8") as handle:
        for session in sessions:
            handle.write(json.dumps(session, allow_nan=False) + "\n")
    rows = [flat_row(s) for s in sessions]
    columns = list(dict.fromkeys(k for r in rows for k in r))
    with (args.out / "sessions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    turn_detections = {json.dumps(s["turn_detection"], sort_keys=True) for s in sessions}
    if len(turn_detections) != 1:
        raise ValueError(f"sessions disagree on turn_detection: {sorted(turn_detections)}")
    summary = {
        "rec": str(args.rec),
        "ref": str(args.ref),
        "profile": arm_manifest["profile"],
        "turn_detection": sessions[0]["turn_detection"],
        "output_rate": args.output_rate,
        "pause_allowance_s": args.pause_allowance_s,
        "sessions_passed": len(sessions),
        "sessions_skipped": skipped,
        "pause_handling": summarize(sessions, "pause_handling"),
        "turn_taking": summarize(sessions, "turn_taking"),
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("pause_handling", "turn_taking")}, indent=1))
    for task in ("pause_handling", "turn_taking"):
        block = summary[task]
        print(f"== {task}: sessions={block['sessions']} any_audio={block['sessions_any_audio']['count']} "
              f"official_tor={block['sessions_official_tor']['count']} commits={block['commits']} "
              f"false_endpoints={block['false_endpoints']['count']} responses={block['responses']}")
        if task == "turn_taking":
            print(f"   official latency mean={block['official_latency_mean_s']}")


if __name__ == "__main__":
    main()
