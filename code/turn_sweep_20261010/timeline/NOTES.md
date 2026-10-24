# Turn-sweep trace analysis: scouting notes (vad500)

Working dir: `/private/tmp/claude-501/-Users-luojiaxuan-Downloads-S2S-omni/d929e068-e502-4614-a422-100edee8e07f/scratchpad/trace_analysis`

Script: `analyze_traces.py` (stdlib only; run with `judge-venv/bin/python -I`).
Outputs: `out/<arm>/sessions.jsonl` (one JSON object per passed session with
per-commit / per-response / per-cut records), `out/<arm>/sessions.csv` (flat
per-session summary), `out/<arm>/summary.json` (arm summary). Two runs produce
byte-identical outputs.

```
judge-venv/bin/python -I analyze_traces.py --rec data/rec/vad500 --ref data/score/vad500/ref --out out/vad500
```

## Data on disk

- `data/rec/vad500/` = `rec-vad500.tar` (sha256 `c7b703b4…88db`, matches
  `MANIFEST.json`) extracted WITHOUT `input.pcm`, `input.wav`,
  `output-media.wav`, `output-playout.wav`. Per session dir
  `samples/<subset>/<id>/input/`: `continuous.jsonl` (trace),
  `input-send-receipts.json`, `manifest.json`, `report.json` (recorder protocol
  verdict + metrics), `playout.json` (recorder's own playout reconstruction incl.
  `cuts`), `transcript.json` (server text deltas). 406 MB.
- `data/score/{vad500,vad800,vad1200,semmed}/ref/` = `score.tar` (sha256
  `71021077…dd69f`, matches). Per sample `<subset>/<id>/`: `output.wav`,
  `output.json` (Parakeet words), `pause.json` or `turn_taking.json`; plus
  `summary.json`, `asr.json`, `manifest.json`, `identity/`, `logs/`. 532 MB.
- Both tars deleted after extraction. `data/` total 938 MB; `out/` 2.2 MB.
- `run.json` for vad500: 335 samples, all `status=pass`,
  `protocol_verdict=pass`; `run.json.samples[].events` already holds the
  annotation windows ([start,end] of each [PAUSE] / the last word).

## Trace format `realtime-legacy-pcm16-v1` (confirmed from the traces)

One JSON object per line: `{"direction": "send"|"receive"|"error"|"admission",
"time_s": <perf_counter seconds>, "event": {...}}`. All times below are relative
to `t0` = `time_s` of the first `send input_audio_buffer.append` (the exporter's
origin). Input end `T` = `t_start_ms/1000` of the last append + its decoded
bytes / (2*16000) = the unpadded input duration. The recorder keeps the socket
open until `T + 1.0 s` (`LEGACY_TAIL_S`), then sends an empty `session.update`
as a liveness probe and closes after its `session.updated`.

Client (`send`) events:
- `session.update` `{event_id, session:{modalities:["text","audio"], turn_detection:{type:"server_vad", silence_duration_ms:500, prefix_padding_ms:300, threshold:0.5}}}` (first), and `{event_id, session:{}}` (probe at `T+1.0`).
- `input_audio_buffer.append` `{event_id, audio:<b64 PCM16 16 kHz, 80 ms = 2560 B>, sglang:{seq, t_start_ms}}`, 52,860 in vad500.

Server (`receive`) events in vad500, with counts and fields:

| event | count | fields |
|---|---|---|
| `session.created` | 335 | `session{id, model, modalities:["text"], input_audio_format:"pcm16", output_audio_format:"pcm16"}`, `event_id` |
| `session.updated` | 670 | `session{…, turn_detection echoed}` (one per `session.update`; second = probe ack) |
| `input_audio_buffer.speech_started` | 770 | `audio_start_ms`, `item_id`, `event_id` |
| `input_audio_buffer.speech_stopped` | 570 | `audio_end_ms`, `item_id`, `event_id` |
| `input_audio_buffer.committed` | 570 | `item_id`, `event_id` |
| `response.created` | 559 | `response{id, object:"realtime.response", status:"in_progress", output:[]}` |
| `response.text.delta` | 22,466 | `response_id, item_id, output_index, content_index, delta` |
| `response.text.done` | 558 | same + `text` |
| `response.audio.delta` | 3,790 | `response_id, item_id, output_index, content_index, delta` (b64 PCM16 **24 kHz**) |
| `response.audio.done` | 362 | `response_id, item_id, output_index, content_index` |
| `response.done` | 548 | `response{id, status:"completed"\|"cancelled", status_details:{reason:"stop"\|"turn_detected"}, usage (null when cancelled), output:[{type:"message", role:"assistant", content:[{type:"text",text},{type:"audio",transcript}]}]}` |
| `output_audio_buffer.cleared` | 418 | `response_id, item_id, event_id` |
| `conversation.item.input_audio_transcription.delta` | 9,670 | `item_id, content_index, delta` |
| `conversation.item.input_audio_transcription.completed` | 548 | `item_id, content_index, transcript` |

No `error`, `admission`, `session.closed` or `response.cancelled` rows occur in
vad500. The legacy protocol has no `sglang.*` receipts.

Observed semantics (vad500, server_vad 500/300/0.5):
- `audio_start_ms` / `audio_end_ms` are positions on the server's input
  timeline (ms of audio appended). `audio_start_ms` of the first
  `speech_started` is 0 (onset minus `prefix_padding_ms`). `audio_end_ms` is the
  detector's speech-end estimate; the `speech_stopped` + `committed` pair
  arrives `silence_duration_ms` of audio later: `commit_time − audio_end_ms/1000`
  is 0.434–0.499 s (median 0.466) across all 570 commits.
- `committed` follows `speech_stopped` (same `item_id`) within <1 ms;
  `response.created` follows `committed` within 0.0–3.4 ms (median 0.6 ms).
  First `response.text.delta` ≈ 83 ms after the commit; first
  `response.audio.delta` 0.15–0.82 s after the commit (pause subset median 0.30).
- Audio arrives in bursts far faster than real time (e.g. pause/10: 9.58 s of
  audio in 12 deltas over 0.67 s). Hence the FIFO zero-buffer playout queue is
  always long and a barge-in cut drops most of it.
- Barge-in: a `speech_started` while a response is active is followed (same
  ms) by `output_audio_buffer.cleared` and `response.done
  status=cancelled, reason=turn_detected`. `cleared` is also emitted after an
  already *completed* response when the server output buffer still holds audio
  (e.g. pause/166). All 418 `cleared` events are within 5 ms after a
  `speech_started`, so the exporter's `speech_started` cut always fires first.
- Swallowed commits: `speech_stopped`+`committed` immediately followed (≤1 ms)
  by `speech_started` with `audio_start_ms ≈ audio_end_ms + 0.21–0.26 s` get no
  `response.created` (11/356 pause commits, 0/214 turn-taking). The resumed
  speech was already inside the 500 ms hangover window but the facade had
  passed the frame boundary.
- Deferred responses: `response.created` with no commit in the preceding 50 ms,
  emitted right after the previous `response.done` (or after the probe ack):
  the facade queues turns (`capabilities.max_queued_turns = 8`). 2 in pause
  (pause/22, pause/179), 4 in turn-taking (tt/38, 40, 61, 69). The script links
  them to the oldest unanswered commit, marks `deferred=true`, and leaves the
  commit-based latency terms null for them.
- 200/216 pause sessions end with speech still open (a `speech_started` without
  `speech_stopped` before the socket closes): the pause clips end while the user
  is talking.

## Exporter cut (`reference_audio.analyze_variant`, same rule as `v15_audio.reconstruct_output`)

- Playout buffer = zeros of length `T * 24000`; each in-window audio delta is
  written at `start = max(cursor, round(at * 24000))`, `cursor = start + n`.
- On `input_audio_buffer.speech_started` (because `turn_detection` carries no
  `interrupt_response: false`) and on `output_audio_buffer.cleared`:
  `cut = round(at*24000)`; if `cut < cursor` zero `[cut, cursor)`, `cursor = cut`.
  So everything queued but not yet "played" at the moment the user resumes is
  dropped; what survives is the audio between its first delta and the cut.
- Deltas received after `T` are excluded; the buffer is cropped at the float
  `T*24000`; then resampled 24 k→16 k and written as `output.wav`.
- `analyze_traces.py` mirrors this per response: `audio_s_received`,
  `audio_s_cut_by_barge_in`, `audio_s_cropped_at_input_end`,
  `audio_s_received_after_input_end`, `audio_s_survived`, `survived_window_s`.
  Cross-check against `score/vad500/ref/manifest.json`: `barge_in_cuts` equal
  for 335/335 sessions, `boundary.queued_audio_cropped_s` equal (to 1e-9) for
  335/335, `output.audio_after_window_excluded_s` equal for 331/335; the other 4
  (pause/7, 25, 51, 170) have no in-window audio so the exporter leaves the
  field `None` while we count 7.2–11.2 s of post-T audio.

## Metric definitions (per session; see `analyze_session`)

- `input_end_s` (T), `session_created_s`, `session_updated_s`, `probe_sent_s`,
  `probe_ack_s`, `last_event_s`, `turn_detection`, `annotation` windows,
  `input_transcripts` (server ASR of the user's committed items).
- `commits[]`: `time_s` (client receipt of `committed`), `speech_stopped_s`,
  `speech_end_s` (= `audio_end_ms/1000`), `speech_end_to_commit_s`,
  `before_input_end` (false endpoint w.r.t. T), for pause handling
  `pause_index_by_commit_time` (commit time ∈ `[pause_start, pause_end +
  allowance]`, allowance = `silence_duration_ms` or `--pause-allowance-s`),
  `pause_index_by_speech_end` (`audio_end_ms/1000` ∈ `[pause_start, pause_end]`),
  `offset_from_pause_start_s`; for turn taking `before_last_word_start`,
  `before_last_word_end`; `response_id`, `response_deferred`,
  `swallowed_by_speech_started_s`, `input_transcript`.
- `responses[]`: `created_s`, `trigger_commit_*`, `deferred`,
  `commit_to_created_s`, `commit_to_first_text_s`, `commit_to_first_audio_s`
  (decision-to-first-packet), `created_to_first_audio_s`, audio accounting
  above, `audio_s_received_before_cut` (deltas before the first interrupting
  `speech_started`/cut), `cut_by`, `cut_s`, `interrupted_by_speech_s`,
  `done_s`, `status`, `status_reason`, `created_to_done_s`,
  `first_audio_to_done_s`, `text` (first 300 chars), `text_chars`.
- `speech_starts[]`, `cuts[]` (type, time, dropped seconds, responses hit).
- `official`: recomputed from `output.json` with the official rule
  (`eval_pause_handling.py` / `eval_smooth_turn_taking.py` at FDB
  3e799c45): `tor` (transcript span ≥ 1 s OR > 3 words), `transcript_words`,
  `transcript_span_s`, `first_word_start_s`; pause:
  `transcribed_speech_in_pause_s` (sum of word∩pause overlap),
  `words_starting_in_pause`, `any_word_starts_in_pause`; turn taking:
  `latency_raw_s = first_word_start − last_word_START` (the official evaluator
  uses `timestamp[0]`), `latency_s = max(0, raw)`,
  `first_word_before_final_commit`.
- `summary.turn_taking`: final commit vs T, vs last-word end/start; final
  response first audio vs T and vs last-word start.
- Arm summary: counts/rates for all of the above plus `n/mean/median/p90/min/
  max` for each latency term, `pauses` statistics, audio totals.

## Reconciliation on vad500 (all exact)

| known | recomputed |
|---|---|
| recorder any-audio pause sessions 157/216 | `sessions_any_audio` 157/216 (≥1 `response.audio.delta` anywhere, incl. after T; equals `run.json media_duration_s > 0`). In-window: 153/216 |
| official pause takeover 30/216 | `sessions_official_tor` 30/216 |
| official turn latency 0.693 s | `official_latency_mean_s` 0.6927731 (TOR 119/119) |
| Candor pauses 277, 0.61–1.49 s, median 0.87 | 277, min 0.61, max 1.49, median 0.870 |
| exporter `barge_in_cuts` / `queued_audio_cropped_s` | identical for 335/335 |

## Why 157 any-audio sessions become 30 official takeovers (vad500 pause subset)

1. 356 commits in 216 sessions (1.65 per session; 215 sessions have ≥1); every
   commit is before T (the clip ends mid-turn), so 100% are false endpoints.
   273/356 commits land inside an annotated pause (commit time rule; 269/277
   pauses get a commit), 83 land in gaps the annotation does not mark (their
   speech end is ≥1 s away from any annotated pause for 77 of them, median
   3.95 s). By the strict speech-end rule only 89/356 are "inside": the VAD's
   `audio_end_ms` sits a median 24 ms *before* the annotated pause start
   (p10 −0.136, p90 +0.054), i.e. the annotation starts the pause slightly
   after the acoustic silence onset.
2. 345 responses: 11 commits swallowed, 2 deferred. 204/345 got audio; the
   other 141 were cancelled by the user's resumption before the first audio
   delta (median 0.24 s after creation; first audio takes median 0.30 s,
   p90 0.52 s after the commit).
3. The user resumes a median 0.87 s after the pause start, the commit comes
   ~0.45 s after it and the first packet ~0.30 s later, so only 137/271
   in-pause responses got their first delta out before the annotated pause end.
4. Of 204 audio responses, 186 (91%) are cut by the exporter at the next
   `speech_started`; audio survives for a median 0.28 s (p90 0.84 s) per
   response. Totals: 813 s received → 564 s dropped by barge-in cuts, 39 s
   cropped at T, 128 s received after T, **83 s survive** in the 216
   `output.wav`s (153 sessions with any surviving audio).
5. Parakeet transcribes ≥1 word in 68/216 sessions; the official rule (span ≥1 s
   or >3 words) passes 30. 16 of the 30 have <1 s of surviving audio and 17 of
   the 30 reach the span threshold only because fragments of two or more cut
   responses are spanned first-start→last-end (e.g. pause/10: "That sounds
   like" at 5.68–6.48 and "so." at 12.56–12.72 → span 7.0 s → TOR=1).
   `sessions_any_word_starts_in_pause` 64/216; transcribed speech inside pause
   windows totals 29.4 s.

## Turn-taking observations (vad500)

- 214 commits / 119 sessions (1.8 per session). Every commit is before T
  because the clips carry ≥4.5 s of audio after the last word
  (`final_commit_minus_input_end_s` max −4.51, mean −4.9), so `before_input_end`
  is not informative here; use `before_last_word_start`: 99/214 commits in
  56/119 sessions fire before the user's last word begins.
- Final commit − last-word end: median +0.18 s (p90 0.38); the VAD's
  `audio_end_ms` is a median 0.28 s before the annotated last-word end.
  Final-response first audio − last-word start: median 0.83 s.
- `commit_to_first_audio_s` median 0.35 s, p90 0.66 (vs 0.30/0.52 in the pause
  subset: longer first answers).
- Official latency 0.693 is biased down by premature responses: in 20/119
  sessions the first Parakeet word comes from a response *before* the final
  commit (18 negative raw latencies clipped to 0). Restricted to sessions whose
  first word follows the final commit the mean is 0.819 s (n=99); single-commit
  sessions 0.776 s (n=64).
- Two sessions where the VAD missed the final stretch of speech: tt/36 (last
  word 14.02–14.40, last commit 13.36, no later `speech_started`) and tt/62
  (T=94 s, last word 88.86–89.0, last commit 79.68; the server ASR of the
  user's items is garbage, suggesting very low-level audio). Both still score
  TOR=1 with latency 0 from an earlier response's surviving audio.

## Caveats for the next phase

- Pause allowance for `semantic_vad` (semmed arm): no `silence_duration_ms`, so
  the commit-time pause window shrinks to `[start, end]`; pass
  `--pause-allowance-s` explicitly if a hangover should be assumed.
- Parakeet word timestamps have ~80 ms granularity and can start up to ~0.09 s
  before the first delta receipt (pause/10: word 5.68 vs delta 5.77).
- `audio_s_received_before_cut` stops at the first interrupting
  `speech_started`; deltas still in flight after a cancel are counted in
  `audio_s_received` only.
- Response↔commit linking uses the 50 ms immediacy rule (observed max 3.4 ms);
  deferred responses are attributed FIFO to the oldest unanswered commit,
  which is an assumption about the facade's queue order.
- Only `status=pass` + `protocol_verdict=pass` sessions are analysed (all 335
  in vad500); skipped ones are listed in `summary.json.sessions_skipped`.
