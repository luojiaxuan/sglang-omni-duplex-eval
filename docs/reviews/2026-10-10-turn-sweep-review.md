# ChatGPT 外审：判轮参数扫描的结论读法（2026-10-10）

- 渠道：网页 ChatGPT 临时会话，模型选择器显示 Pro 档（思考强度滑杆最右端），回复标注"思考了 13m 34s"。
- 附件：`docs/runs/2026-10-10-turn-sweep-qwen3omni.md`（审前版本 a5bf28da…4783c4fd）、`docs/runs/2026-10-09-fdb-native-eval.md`、`docs/runs/turn-sweep-20261010/summary.json` 与四个 `score-<arm>-summary.json`。
- 审前判断（写在 run doc 的"读法"里）：(1) 500 ms 静音在停顿上远好于 Nemotron 原生、延迟只差 0.14 s，对 MiniCPM-o 两项都好；(2) 延迟减阈值约 0.2–0.3 s 是服务端开销；(3) 语义判轮 medium 被静音判轮支配。
- 处置：见 run doc 15:30 PT 之后的"读法"修订与本文末尾的采纳记录。公式在网页文本提取中被压平，原样保留。

## 回复全文

(a) Caliber traps
1. The pinned code measures qualified transcript output, not every opening or detector decision.

Let m be the number of ASR word chunks, D the span from the first word's start to the last word's end, W the first output word's start, and E = input_turn[0]["timestamp"][0]. The operative qualification is

Q = 1{ m > 0 ∧ ( D ≥ 1 s ∨ m > 3 ) }.

The pause evaluator substitutes the last word's start when its end timestamp is null.

| Metric | Actual estimand | Consequence |
| --- | --- | --- |
| Pause takeover | ∑Q/N, using the whole exported output transcript; no pause annotation is consulted | Not "fraction of pauses interrupted," false endpoint rate, or probability of any audible interruption |
| Turn-taking takeover | ∑Q/N | Does not require that the qualifying response begin after E |
| Turn-taking latency | ∑_{Q=1} max(0, W−E) / ∑Q | Conditional on qualification; early starts receive zero; silence/nonqualifying output receives no latency |
| Speech qualification | Transcript span ≥1 s or >3 words | Several separated backchannels can jointly qualify; a prematurely interrupted ≤3-word, <1 s response does not |

These are task-module semantics at the revision recorded in the summaries, not merely properties of the evaluate.py dispatcher.

2. Reconstruct the actual denominators before comparing latency.

| Arm | Pause takeovers / evaluated | Turn takeovers / evaluated | Latency denominator | Conditional latency |
| --- | --- | --- | --- | --- |
| 500 ms | 30/216 | 119/119 | 119 | 0.692773 s |
| 800 ms | 10/216 | 118/119 | 118 | 1.043136 s |
| 1200 ms | 4/215 | 119/119 | 119 | 1.479664 s |
| Semantic medium | 8/214 | 118/119 | 118 | 2.012288 s |

Counts are reconstructed from the exact rates and evaluated populations.

The rounded native rows imply Nemotron 84/216 pause takeovers and 111/119 turn takeovers, versus MiniCPM-o 38/216 and 101/119; their latency means therefore describe different responder populations from Qwen's 119/119.

The reported arithmetic is correct: 500 ms versus Nemotron gives approximately −25.00 percentage points pause TOR, +0.13577 s conditional latency; versus MiniCPM-o, −3.70 points, −1.32023 s. These are cross-system point differences, not an identified causal "latency cost of improved pause handling."

3. Hard gating is a legitimate system advantage, but not evidence of model-level turn understanding.

FDB selects Candor turns containing internal pauses of 0.4–1.0 s, while turn-taking examples receive 5 s of terminal silence; a 1.2 s timer sits above the selected pause band and comfortably inside the response allowance. This construction favors duration-based separation without requiring semantic completion prediction; it does not establish that every pause in every retained clip is ≤1 s.

A detector-triggered system can obtain low pause TOR through waiting, delayed generation, cancellation, or muting rather than correct endpoint classification; conversely, its mandatory waiting can disadvantage genuine post-turn latency. Comparing those deployed policies is valid; attributing their differences to half-duplex versus native model architecture is not, because the generator, runtime, and gating policy all change.

The two selected tasks do not measure interruption recovery, backchannel usefulness, retained comprehension of resumed speech, or response relevance; the sweep explicitly excludes the other subsets and content judging.

4. The legacy renderer adds a particularly important cancellation interaction.

The referenced legacy exporter cuts queued playout on output_audio_buffer.cleared, or on speech_started when interruption is enabled; consequently, a false endpoint followed by user resumption can leave little qualifying speech in the exported WAV. Audit false commits, generated audio, canceled audio, and audibly played audio separately; establish that simulated cancellation matches the intended application player before treating the result as user-perceived behavior.

The whole-transcript rule also disadvantages native systems that produce several harmless acknowledgments separated in time; "native pause takeover" is not necessarily a sustained interruption at the annotated pause.

5. Early-start clamping favors aggressive systems; the 0.896 s substitution is not a valid correction.

The native diagnostic identifies 11/119 early-start samples, reports 100 responding samples among 108 eligible, and changes the latency to 0.896 s; the document explicitly says the two scoring paths differ in gates, windows, and VAD implementation.

Even assuming those 11 samples correspond exactly to 11 upstream zero-latency responders, removing only those zeros would yield 0.557 × 111 / (111 − 11) ≈ 0.618 s, not 0.896 s; the approximately 0.339 s discrepancy cannot be attributed solely to removing early starts.

Do not assume the half-duplex arms have zero early starts: a VAD decision during an internal pause can precede the annotated final boundary. Apply the same signed-onset and early-response accounting to every arm.

6. Separate response-onset censoring from response-offset censoring.

Exports stop at [0, T_input]; late responses can be absent or too short to qualify, lowering turn TOR while excluding their latency, and delayed pause responses can disappear outside the scored window. A slower system can therefore receive both a better conditional latency mean and a worse response rate through selection; silence, late output, brief output, and ASR failure are not distinguished by TOR alone.

Nemotron's 83/119 samples still speaking at window end demonstrate censored response offsets, not 83 unobserved response onsets; do not discard those samples or claim that this count alone invalidates onset latency.

A longer recording timeout does not lengthen the fixed scoring window; the legacy client's post-input liveness tail is likewise distinct from exported exposure time.

7. The three failures are informative exclusions, but they do not contaminate the 500 ms denominator.

There are three failed arm-sessions across two distinct clips: /202 fails under 1200 ms and semantic medium; /93 fails under semantic medium. All are pause samples; 500 ms has no failures, and no turn-taking denominator loses a technical failure.

| Arm | Complete-case pause TOR | All-216 bounds, assigning missing outcomes 0 or 1 |
| --- | --- | --- |
| 1200 ms | 4/215 = 0.018605 | 4/216–5/216 = 0.018519–0.023148 |
| Semantic medium | 8/214 = 0.037383 | 8/216–10/216 = 0.037037–0.046296 |

These bounds derive from the documented exclusions; they remain disjoint, so missing outcomes alone cannot reverse the observed 1200 ms–semantic pause ordering.

Dropping these cases conditions on detector-dependent buffer survival, not random missingness; assigning a crash an adverse outcome defines a takeover-or-technical-failure composite, not an observed takeover. Preserve complete-case TOR, technical-failure rate, and all-intended-case sensitivity results separately.

8. "Same evaluator" does not establish capture, configuration, or deployment parity.

| Trap | Evidence and required restriction |
| --- | --- |
| Different export path | The sweep uses an unpublished local merge with trace-format, sample-rate, and eligibility patches; freeze and apply one export implementation to every comparator. |
| Different protocol guarantees | Legacy capture lacks native accepted/ended/drained receipts; its liveness probe does not prove equivalent internal processing of every input frame. |
| Incomplete configuration verification | The client verifies echoed detector type, not all numeric thresholds or medium's internal mapping; do not infer either correct numeric settings or silent fallback from the label alone. |
| Timing representation | Pin pacing, clock origin, arrival-order FIFO playout, output resampling, leading silence, and cancellation; an ASR word timestamp is not first packet, first acoustic energy, or server compute completion. |
| MiniCPM-o provenance | Its numbers are reused from PR #2377, server 6eed7bd; the native document explicitly says they are not a same-condition comparison, contradicting the sweep's stronger framing. |
| Runtime and hardware attribution | Qwen uses a newly exercised single-GPU colocated layout and one arm per GPU; Nemotron uses another server revision, and MiniCPM-o has its own decoding/listening settings. Rotate device assignments and distinguish deployment comparisons from architectural claims. |
| ASR reproducibility | Nemotron's graph-on/off transcripts were explicitly checked and identical; do not invoke that bug as an established explanation for its score. Require equivalent checkpoint/runtime evidence for each new capture. |

9. One run and aggregate summaries cannot establish uncertainty or paired superiority.

The MiniCPM-o pause advantage is only eight net outcomes among 216 clips; the summaries contain neither paired disagreement identities nor latency distributions. Under an independent-clip binomial calculation, illustrative 95% Wilson intervals are 9.9–19.1% for 30/216 and 13.1–23.2% for 38/216; these are not a paired comparison or an estimate of run-to-run variability.

One run per arm leaves stochastic decoding, warm-up, device effects, and runtime variability unestimated; choosing the attractive operating point from the same sweep also requires separating exploratory selection from confirmation. The document's "differences below 5%" rule supplies neither confidence intervals nor a significance criterion.

(b) Strongest alternative explanation for semantic medium
10. Prioritize conservative endpoint policy or integration delay over slow classifier inference.

Smart Turn is designed to run after a lightweight VAD detects silence; its authors report approximately 65 ms inference in one Pipecat Cloud configuration, not this deployment. A minimum-silence gate, conservative completion threshold, deferred recheck, or fallback timeout can produce a roughly 2 s endpoint delay with fast individual classifier calls; the attached summaries contain no timestamps that distinguish these mechanisms.

FDB's selected pause-duration band gives a plain timer an unusually favorable operating region; semantic medium can therefore lose this benchmark comparison through calibration rather than computational slowness. Do not claim that Candor endpoints are mislabeled: the paper describes manual review using both conversation channels.

A second, directly motivated confound is different generator input segmentation: semantic mode retains utterances long enough to hit the 30 s limit while silence thresholds split them. Longer Qwen input/prefill or different accumulated context could increase decision-to-word latency without slow Smart Turn inference.

Verify 16 kHz mono input, retention of the latest approximately 8 s, and left-padding of shorter inputs before interpreting completion probabilities; these are the model's documented input conventions, not verified properties of the private runtime.

(c) Minimal decisive measurement within one 4-hour, 4-GPU lease
11. Spend the lease on five arms and event attribution, not another broad threshold sweep.

| Item | Instruction |
| --- | --- |
| Arms | Run Qwen-500, Qwen-1200, Qwen-semantic-medium, Nemotron, MiniCPM-o; 800 ms and semantic low/high are unnecessary for the stated pairwise claims. |
| Repetitions | Run two fresh passes of all 335 clips per arm: 3,350 sessions; retain existing recordings as historical replication, not interchangeable same-condition observations. |
| Scheduling | Duration-balance each arm/pass into shards; dynamically schedule across four GPUs, one active session per GPU, with arm/device rotation and fixed per-system decoding configurations. |
| Exposure | Preserve the original input and scored prefix; append 5 additional seconds of silence to turn-taking inputs only, yielding approximately 10 s post-turn observation. |
| Budget | At the documented approximately 1.2 h/suite: 10×1.2 + 10×119×5/3600 = 13.65 GPU-hours; using the observed 77-minute sweep duration conservatively gives 14.49 GPU-hours, leaving approximately 23 wall-clock minutes for staged startup, scoring, and targeted probes. |
| Admission condition | Pre-stage weights, containers, instrumentation, and scoring; verify the actual duration sum before starting and never truncate slow sessions selectively to meet the lease. |

12. Record a per-clip event timeline sufficient to identify the latency terms.

Record input sample indices and monotonic timestamps for last VAD speech, each endpoint-candidate trigger, classifier enqueue/start/end, completion probability, decision reason, commit, Qwen input length, generation start, first output packet, first played speech, first ASR word, cancellation, and window close; preserve response IDs linking each output to its triggering commit.

Record actual resolved detector configuration, Smart Turn weight hash and execution provider, queue depth, cumulative sent/processed audio, output backlog, and all failure statuses; a successful type echo alone is insufficient.

For native models, measure first speech, not first audio packet; retain continuous silent output without confusing it with a response.

13. Emit two score products from each capture.

| Product | Required contents |
| --- | --- |
| Frozen FDB result | Independently transcribe the original [0,T_input] WAV and run the pinned scorer unchanged; do not transcribe extended audio and merely filter timestamps, because that changes ASR context. |
| Diagnostic result | Per-clip signed first-word onset; first substantial response after the boundary; early speech versus early takeover; false commits; canceled bursts; any audible pause intrusion; qualifying TOR; technical failures; onset censoring; offset censoring. |
| All-intended-case timing | Response-by-deadline rates at 1, 2, 5, 10 s, with early takeovers and failures explicitly accounted for; retain conditional means as secondary metrics. |
| Paired inference | Paired outcome tables and 95% intervals for the three specified contrasts; cluster by source conversation where available and nest repeats within clips rather than treating repeated clips as independent new samples. |

Do not extend the pause-scoring window into legitimate post-turn answering and count those answers as pause failures.

14. Resolve the semantic mechanism with one targeted intervention.

Replay a small, predeclared diagnostic set covering slow semantic responses, timer/semantic disagreements, and /93 plus /202; compare ordinary medium behavior with a completion-gate bypass at the first eligible semantic check, leaving the input prefix and generator configuration unchanged.

Use the event timeline to distinguish: late first invocation → trigger policy; fast negative predictions followed by waiting → completion calibration/fallback; long classifier execution → inference implementation; normal decisions but slow subsequent output → Qwen/runtime/playout.

Replay overflow cases with a raised buffer limit only as a separately labeled diagnostic; preserve original-limit failures in the primary comparison.

Declare dominance only for the prespecified metrics and population when paired uncertainty supports it; otherwise return "point ordering reproduced; superiority not established." Repeating the same 216 clips reduces execution uncertainty but does not create additional independent conversational cases.

(d) Reviewer-rejectable readings and replacements

| Run-doc reading | Required replacement |
| --- | --- |
| L27: takeover means "the model opens its mouth." | Use "the exported transcript satisfies the pinned takeover rule"; distinguish any audible intrusion, false endpoint, and qualified takeover. |
| L40: latency minus threshold is server overhead after turn detection. | Report only threshold-subtracted FDB latency: 0.192773 / 0.243136 / 0.279664 s; no commit timestamps support the causal decomposition. |
| L41: semantic medium is dominated by "silence thresholds." | 1200 ms empirically dominates this medium configuration on the reported point metrics; 800 ms does not, because 0.046296 pause TOR is worse than 0.037383. The 1200 ms latency advantage is 0.532624 s; population-level or Smart-Turn-wide dominance remains untested. |
| L42: turn-based systems beat native systems on both metrics; native models did not achieve lower latency. | Nemotron's reported 0.557 s is lower than 0.692773 s; this is a pause–latency tradeoff, not two-metric dominance. MiniCPM-o has a favorable point comparison but explicitly unmatched provenance. |
| L42: 0.896 s supplies a corrected apples-to-apples native latency. | Keep it as a different diagnostic estimand; reproduce the same timestamp, window, and eligibility rules across systems before comparison. |
| L42: the silence threshold is an unconditional FDB latency floor. | The floor applies relative to the detector's own last-speech boundary under the assumed trigger path; annotation offsets, earlier commits, and zero clipping prevent an unconditional floor relative to FDB's E. |
| L43: ignore differences below 5%. | Replace the arbitrary cutoff with paired counts, latency distributions, confidence intervals, and repeat variability; specify percentage points versus relative percentages. |
| L27/L43: failed sessions are "counted as failures." | State explicitly that failures are counted operationally but excluded from behavioral denominators, with no behavioral penalty; report the three arm-session failures and two affected clip IDs. |
| L49: a named local scoring branch establishes reproducibility. | Publish the exact merged-tree revision or patch, runtime code access, resolved configurations, and detector-weight hashes; distinguish artifacts documented as archived from code actually available to a reviewer. |

For L40's replacement, with V the detector's last-speech boundary, C its commit time, and W the ASR word onset, the unclipped per-sample identity is

(W − E) − θ = (V − E) [boundary mismatch] + (C − V − θ) [trigger/scheduling residual] + (W − C) [generation, transport, playout, word onset].

Apply this identity only to an output associated with that commit; averaging clipped, responder-conditioned FDB latencies does not identify the final term.

## 采纳记录

见 run doc 的"读法（外审后修订）"一节：采纳 1、2、3、4、5、7、8（MiniCPM-o 口径）、9、10 与 (d) 全部替换；对 6 的"追加 5 秒静音"与 11 的"五臂两遍"作为下个租约的候选设计，不在本次改判范围。它反对但我坚持的：无。
