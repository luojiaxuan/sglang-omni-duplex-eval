# 外审:判轮离线扫描(2026-10-04 PT,ChatGPT Latest / Pro,思考 17m40s,临时聊天)

送审材料:design_note.md(自己的判断)、benchmarks/cascade_replay 下的 README.md、sweep.py、turn_log.py、eou_log.py(提交 e9fa603 之前的版本)、SoulX `service/model.py`@a0b9063、FDB `eval_pause_handling.py` / `eval_smooth_turn_taking.py`@3e799c45。
以下为回复原文(公式由网页抽取后整理,内容未删改)。

---

1. Exactness: first-commit index is defensible; first-audio time is not

1.1. State the theorem as a common-prefix stopping-time result. Let h_k contain model state, ASR state, buffers, and randomness; let z_k^θ contain policy-local counters. A single trace identifies τ_θ = min{k : g_θ(h_k, z_k^θ) = COMMIT} exactly only when every nonterminal policy transition preserves the same h_{k+1}, policy-local counters do not alter model inputs before commitment, and input bytes/initial states match. This proves a first-commit index, not service-return time, first PCM, first audible speech, or official TOR. The proposed argument establishes only equality of the WAIT embedding, not all these conditions. [design_note]

1.2. SoulX has policy-dependent nonterminal behavior. At a decision with speech_detected=False, selecting complete resets the model without replying; selecting incomplete preserves state and starts monitoring. Thus "no reply yet" does not imply "same state trajectory." Certify this condition unreachable for the pinned configuration, or branch/replay affected policies; counting occurrences alone does not repair exactness. [soulx_service_model, sweep]

1.3. Semantic-VAD equivalence is narrower than "any threshold." Fix Silero threshold, candidate timing, preprocessing, context window, and failure behavior; then varying EOU confidence tiers and silence requirements can share pre-first-end scores. Changing the Silero threshold changes first-speech position, silence runs, query times, and potentially EOU input. The logger fixes these at 0.5, 160 ms, and an 8 s suffix. [eou_log]

1.4. The ordinary semantic-VAD controller is substantially reproduced correctly. Inspected upstream code caches one EOU prediction per silence run; it does not continually reconsider scores. Therefore the logger's 2400 ms scoring cap does not invalidate the low preset's 3000 ms fallback: that path needs only the first score. Pin the deployed upstream SHA; current upstream inspection is not checkout verification. [GitHub, sweep]

2. Code defects and exactness blockers (P0 = blocker for the advertised exactness or primary metric)

| ID | Pri | Defect / demonstrated consequence | Required change |
|---|---|---|---|
| B1 | P0 | The forced-WAIT logger can still reply. Outside decision, raw <\|user_complete\|> passes through unchanged; the inherited handler performs ASR, returns speak, and resets. The sweep ignores that unconditional stop and observes post-reset speech_detected=False. Injected trace: logger speaks at 0.160 s; sweep returns None. | Record pre-transition state and unconditional complete events. Treat such an event as a common stop for all surviving policies and truncate, or suppress it only after recording its stopping semantics. Assert the intended logging invariant. |
| B2 | P0 | Raw <\|user_incomplete\|> is mishandled. Production enables monitoring and resets wait_idle_cnt=0; the sweep neither starts nor resets its counter unless decision=True. Injected traces: wait=1 should stop at 0.320 s, but sweep misses; an existing-counter reset should stop at 0.800 s, but sweep stops at 0.640 s. | Reproduce transitions for every returned state. Share the transition implementation with production. |
| B3 | P0 | Rounded scores invalidate exact comparisons. SoulX logits rounded to 4 decimals; Silero to 3; EOU to 4. 0.4996→0.500 changes silence to speech and shifts the candidate lookup (KeyError in a constructed trace). EOU 0.87996→0.8800 changes medium-preset commitment from 2.048 s to 0.672 s. | Serialize losslessly; record the exact speech Boolean; rounded logs need ambiguity bounds. |
| B4 | P0 | Pause takeover ignores time: metrics() returns mean(reply is not None), ignoring user_end, compute, backend delay, output horizon. | Define commitment vs audible onset; compare against the protected interval; keep "any commitment anywhere" only under that explicit name. |
| B5 | P1 | One initial seed does not establish identical per-sample state: reset() samples three random buffers; sharding, skipping, earlier resets change RNG position. | Deterministic per-sample initialization shared by logger and replay; record fingerprints; test order/shard invariance. |
| B6 | P1 | Population silently shrinks: keys = set(soulx) & set(eou). Existing outputs skipped without config validation. | Authoritative manifest; fail/report missing samples; verify metadata before joining. |
| B7 | P1 | Calibration incomplete and non-enforcing: only (0,8), skips missing files, no Candor-pause mapping, reports mismatches only. | Compare integer chunk IDs; require full coverage and zero unexplained mismatches; cover other families and edge paths. |
| B8 | P1 | Some grid configurations invert confidence behavior: conf_ms=960, max_ms=800. | Constrain tier ordering or label the inverted family. |
| B9 | P1 | EOU failure behavior not replayed (upstream switches to sticky fixed-silence fallback). | Log failures/fallback state. |
| B10 | P1 | Input/config parity assumed: SoulX gets float audio, EOU requantizes to PCM16; token IDs from tokenizer vs configured IDs; tail handling differs. | Assert identical production inputs and conventions. |

2.1. The wait counter is not off by one: the first gated idle sets the counter to zero; wait=8 means eight additional idle chunks (nine chunk intervals in a fully silent toy sequence). Backchannel sets the counter to 1, so "eight consecutive idle chunks" is inaccurate.

2.2. The decision gate is not only nonidle→idle: mistake_len >= max_mistake_num can invoke it while the raw prediction is nonidle; stratify these forced decisions.

2.3. The documented --backend override does not exist in argparse.

3. Timing errors are independent of stopping-index exactness

3.1. Reconstruct scheduling: F_k = max(a_k, F_{k-1}) + c_k. Five 160 ms arrivals with 200 ms processing finish at 1.160 s; the sweep's chunk_end + compute gives 1.000 s.

3.2. Forced-WAIT computation omits terminal work: both SoulX reply branches call cascade_asr.recognize(...) and reset before returning speak; the logged compute cannot give exact first-reply latency. The oracle's 41/54 ms does not include it.

3.3. Semantic-VAD compute accounting drops deferred EOU work (extra is reset every frame). Model score readiness explicitly; do not always add the whole EOU duration.

3.4. A 32 ms decision grid is not a 32 ms delivery clock: with 160 ms transport a decision cannot be emitted before its packet arrives (up to 128 ms artificial advantage).

3.5. Contention and a fixed backend correction do not give a conservative bound; measure first PCM and first non-silent playout; the warm oracle median does not establish "speculation saves at most ~50 ms".

3.6. First commitment need not produce the first audible reply (cancellation before audio).

4. Metric definitions reviewers can reject

4.1. The official pause scorer: TO = 1[n > 0 and (span >= 1 s or n > 3)], over the whole output; it does not inspect resumption, pause annotations, or individual replies. len(chunks) is words only if the ASR adapter yields word chunks.

4.2. "Any commitment in the scorer's whole window" upper-bounds official TO; "any commitment before user_end" does not necessarily.

4.3. Official turn-taking latency can anchor to a backchannel rather than the substantive reply.

4.4. Conditional non-premature latency is selectable: removing premature and missing samples gives different denominators; raising the margin cannot advance any first commitment, yet the conditional P50 can fall. Report paired per-sample changes and full-denominator success curves.

4.5. Replacement metric bundle (E_i boundary, C_i first commitment, A_i first audible onset, H horizon, ε annotation tolerance): boundary risk P(C−E < −ε); timely success G_C(d) = N^-1 Σ 1[−ε ≤ C−E ≤ d] at 0.25/0.5/1/2 s with premature and missing counted as zero; miss vs right-censoring; pause hold violation inside annotated intervals plus "any pre-end commitment" as a coarse diagnostic; error severity (lead time, speech vs internal silence); first-failure survival for multiple pauses; measured A−E and cancellation-before-audio; legacy official TOR/latency alongside; deployment cost.

4.6. Validate scorer inputs (None timestamps, zip mispairing, division by zero).

4.7. Treat the sweep as model selection: 243 policies on small sets; choose on grouped dev data, evaluate frozen choices on held-out groups, paired cluster bootstrap; a same-test-set Pareto envelope is descriptive.

4.8. "Entire-curve dominance" exceeds the search: integer margins omit breakpoints; the semantic grid disables the immediate tier except at presets.

5. Missing baselines, ablations, datasets

- P0: never-reply, oracle-boundary, immediate-on-eligible-boundary, semantic-only/no-timeout controls. Label large-margin SoulX as "SoulX-state timeout", not acoustic VAD. Same downstream contract (ASR, LLM, TTS, cancellation, packet clock) for all end-to-end baselines. Controlled backend holds (0/250/500 ms).
- P1: a text-semantic baseline on causal ASR prefixes (pinned LiveKit multilingual text model or FireRedChat EN/ZH detector); one-shot vs re-scored Smart Turn every 160 ms; ablate candidate delay, confirmation duration, VAD threshold, context length; causal vs reference ASR prefixes.
- 5.2: the Chinese TOR gap vs the paper (IndexTTS-1.5 vs Qwen3-TTS backend) is a system discrepancy until decomposed into attempt → audio → qualifying output.
- 5.3: audit Candor "premature" events for legitimate earlier yield points; natural Mandarin conversation; paired-prefix hold/yield cases; FDB v1.5 backchannel/interruption; small FDB-v2.
- 5.4: keep domain pairings explicit; report Candor, synthetic EN, synthetic ZH separately.

6. Replacement plan

6.1 Publish "exact first-commit replay under a verified common-prefix controller", with measured deployment latency and official end-to-end outcomes separately; not "exact first-audio curves".
6.2 One pure controller transition function shared by production, logging, sweeping; log pre/post state, raw vs forced tokens, counters, reset reasons, offsets, fingerprints.
6.3 Exhaustive differential tests over controller cases.
6.4 Select policies under explicit constraints on dev data; evaluate on held-out groups.
6.5 End-to-end runs are measured anchors (defaults plus knee points, both languages), not a calibration function.
6.6 fdb_meta.py, replay.py and ASR adapters were not attached.
