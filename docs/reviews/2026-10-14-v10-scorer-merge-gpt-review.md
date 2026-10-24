# ChatGPT 外审：#2808 打断评分的 VAD 门控（2026-10-14）

- 渠道：网页 ChatGPT 临时会话，GPT-6，思考强度 Pro，回复标注"思考了 21m 4s"，02:00 PT 前后发出。补的是同日上午因登出未能进行的外审（见 `2026-10-14-v10-scorer-merge-review.md`）。
- 附件：`final_design.md`（最终设计、数据与我的判断）、#2808 的 `unified_v10.py`（bd65795）、`full_duplex_metrics.md`、官方 `eval_user_interruption.py` 与 `eval_backchannel.py`、`sweep-speaking-at-end-jit.jsonl`、`compare-unified3-vs-4.json`。附件副本在 `docs/runs/2026-10-14-vadgate/`。
- 审前判断：写在 `final_design.md` 的 Decisions 一节（R 时刻判定、没打断到的样本当未知、轮转不加 VAD、附和不移植）。

## 回复全文

1. Interruption rule and cross-system comparison

1.1. Defensible as an onset-conditioned, endpoint-clear response proxy; insufficient as an interruption-handling success metric. speaking_at_end establishes detector occupancy at R, not whether the system reacted to the interruption, stopped promptly, remained silent while listening, or changed its answer. The implementation and documentation acknowledge some limitations but overstate others with "nothing was interrupted" and "had not yielded." Replace those interpretations with the measured acoustic conditions.

1.2. Executed pure-function counterexamples expose the rule's exact scope. Below, S=2, R=4, T=8; intervals are supplied VAD segments, not waveform-level detector tests; ASR starts at 4.2 unless specified. These outcomes follow unified_v10.py:184-209.

| Supplied VAD segments | Actual scorer output | Attack |
|---|---|---|
| [1,3.999), [4.2,5) | response, latency 0.2 s | Talking through 1.999/2 s of the interruption passes. |
| [1,2.2), [2.7,3.8), [4.2,5) | response, latency 0.2 s | Stopping, restarting during the user's interruption, then stopping again passes. |
| [2.2,4.5) | not_exercised | Starting during the interruption and talking across R disappears from exercised performance metrics. |
| [1,2.2), [4,5); ASR start=4 | speaking_at_end | A fresh reply beginning exactly at R fails, unlike turn-taking's acceptance of starts exactly at E. |
| [1,2.2), [4.2,5); no ASR words | no_response | "No response" does not establish acoustic silence. |
| [1,2.2); ASR start=4.2 | response, latency 0.2 s | An ASR word suffices without detected post-R speech. |

1.3. w=0 avoids one additional parameter; it is not parameter-free measurement. Current upstream Silero uses 512-sample frames at 16 kHz, two-sided padding, minimum-duration filtering and an exit threshold distinct from the entry threshold. Padding can move a post-R onset across R; filtering a newly begun segment shorter than 250 ms can erase evidence that speech was interrupted successfully. Thus full-file "speech at S" can depend on what happens after S. These are upstream-source implications, not a replay of the package version used for your results.

1.4. Keep the endpoint diagnostic; do not substitute an arbitrary end-window as the principal fix. R-S>=1.7 s provides an opportunity to stop but also permits a nonreactive answer to finish naturally before R. Add first detected cessation latency from S, speech-overlap seconds/fraction over [S,R], and pre-R restart counts; censor cessation at recording truncation rather than treating truncation as a stop. A cessation curve still needs a matched muted-interruption control to distinguish reactive stopping from natural completion.

1.5. Preserve observable behavior on non-exercised samples. Compute and emit speech_at_onset and speech_at_end independently for every eligible sample before choosing the mutually exclusive outcome. The current onset-first branch prevents recording an observed R violation when S is silent; treating interruption capability as unknown does not make the actual endpoint occupancy unknown.

1.6. Unknown rather than failure is defensible for untested capability, but the estimand needs qualification. For the actual fixed-S experiment, interruption handling on a non-exercised sample is structurally untested, not an ordinary missing observation of the same event. selected_bounds are valid worst-case completions of an explicitly hypothetical binary outcome; they do not automatically bound performance under a different, forced-exercise protocol. Counting every non-exercised sample as an interruption failure instead would conflate answer timing/length with interruption handling.

Let N=selected, M=eligible, E=exercised, I=N-M, and C=successful exercised samples; the implementation implies:

| Quantity | Observed value | Unknown count in selected bounds | Selected bounds |
|---|---|---|---|
| Exercise | E/M | I | [E/N, (E+I)/N] |
| Interruption performance | C/E | I+(M-E) | [C/N, (C+N-E)/N] |
| Observed exercised-and-successful yield | C/N | Not required to define this observed subevent | Do not relabel it overall capability |

The first two rows reproduce rate/subset_metrics; the third identifies the meaning of the performance lower endpoint, not a proposed correction for selection bias.

1.7. Cleanest comparison from existing recordings: a paired common-exercise contrast plus an explicit selection report, not a corrected scalar. The documentation's pairing recommendation is correct but incomplete as a reporting specification.

| Required component | Specification |
|---|---|
| Fixed population | Use identical selected sample_ids; retain failed/missing captures as unavailable rather than silently changing N. |
| Primary paired contrast | On samples eligible and exercised in both systems, define Y_i(k)=1 only for a valid response within k; report mean(Y_A-Y_B) with a paired bootstrap interval. |
| Horizon | Require adequate observation through R+k for a k-second comparison, or explicitly retain the finite-window lower-bound interpretation. |
| Selection | Report each system's eligibility/exercise rates, common-exercise count, and the exercise table (both, A-only, B-only, neither) among jointly eligible samples. |
| Broader target | Report marginal conditional rates and selected bounds separately; neither multiplying nor dividing by exercise rate identifies latent capability. |
| Multiple systems | Pair-dependent intersections do not define one common leaderboard population; use a fixed common population or a separately defined controlled protocol. |

Pairing controls item composition within the common subset, not selection into that subset; the supplied documentation already disclaims selection-bias removal and insufficient observation horizons.

For the same hypothetical completion target on identical selected IDs, marginal intervals [L_A,U_A], [L_B,U_B] imply difference bounds [L_A-U_B,U_A-L_B]; superiority under every completion requires L_A>U_B for a higher-is-better score. This is algebraic worst-case uncertainty, not a 95% confidence interval.

1.8. For a general interruption-capability claim, change the experimental protocol. Trigger interruptions after a standardized speaking-state criterion, balance interruption content and utterance position, retain equal post-R horizons, and report failures to establish the speaking condition separately. Use matched interrupted/muted runs with identical pre-S history; state-triggering alone does not eliminate differences in interruption difficulty. The current evidence cannot validate cross-system interruption rankings because only Nemotron has interruption recordings.

1.9. The dominant uncertainty is exercise selection, not the reported threshold sweep. The 2-second rate's selected bounds span 43.5 percentage points [0.540,0.975], versus approximately 8.0 points for its conditional Wilson interval [0.901,0.981]; the sweep spans 1.1 points in response rate but 25% in endpoint-failure count, 4->5, and 80 ms in median latency, 1.12->1.20 s. Aggregate stability does not establish stable sample identities or detector correctness.

The 83 prior-speech cases and median 1.317-second gap support "speech ended before S," not the stronger semantic claim "the answer had finished"; the four remaining cases establish no detected pre-S speech, not necessarily no speech throughout the recording.

2. Implementation/document audit

| Finding | Location | Required correction or interpretation |
|---|---|---|
| Core rate/latency implementation matches the intended convention. | unified_v10.py:413-465 | Non-exercised rows leave performance denominators; speaking_at_end remains a scored failure; missing valid-response latency becomes infinity; no_response_rate counts only its named outcome. The median is not responder-only. |
| Outcome definitions are not literally disjoint. | full_duplex_metrics.md:67-70; unified_v10.py:203-206 | Add "speaking at S and R" to speaking_at_end; state onset-gate precedence and half-open VAD intervals [start,end). Currently a sample silent at S and speaking at R satisfies two prose bullets but becomes not_exercised. |
| The global unknown-count definition incorrectly includes non-exercised rows for exercised_rate. | full_duplex_metrics.md:104; unified_v10.py:444-451 | Explicitly exempt exercised_rate: its non-exercised rows are known false, not unknown. The real result [0.565,0.565] confirms the implementation's correct exception. |
| "No response means silence" overclaims the ASR observation. | full_duplex_metrics.md:50,59,70; unified_v10.py:156-181,188-209 | Replace with "no transcribed word"; detected post-R speech can coexist with no_response, and an ASR-only word can establish response. |
| The post-R constraint is enforced upstream of interruption_sample, not inside it. | unified_v10.py:265-271,275-296 | Valid internal contract, not a missing-filter bug: score_eligible rejects words before R before invoking the sample function. Direct callers must preserve that contract. |
| Audio duration is not locally checked against T; endpoint censoring is untreated. | unified_v10.py:77-97,258-264 | Format checks enforce 16 kHz/mono/PCM16, not frames/16000 == T. R=T is accepted; with audio ending at T and half-open segments, speaking(R) must be false. Validate the export-duration invariant and mark an unobserved endpoint unavailable rather than silent. |
| Non-null word ends are unchecked. | unified_v10.py:69-74,226-272 | Probes with end<start, end>T and end=inf pass timestamp_problems; those ends can affect pause overlap/carry-in. Validate finite ordered ends and define any permitted clipping. |
| Hash checks establish file consistency, not complete ASR provenance. | unified_v10.py:475-510 | Transcript hashes are checked against asr.json and annotation/audio hashes against the manifest, but ASR is not bound to the current manifest/annotation version. Add the binding or document/test the caller's precondition. |
| Documented reference-column hash suppression is outside the supplied implementation. | full_duplex_metrics.md:120; unified_v10.py:628-655 | render neither checks summary hashes nor emits input-change warnings; verify the unsupplied caller. |
| This renderer cannot display the official backchannel reference. | unified_v10.py:482-486,630-651 | Scoring skips backchannel, and rendering iterates only unified subsets. Render official-only subsets separately or state that their reference appears only in another report. |
| VAD loading is unconditional; reproducibility is environment-dependent. | unified_v10.py:481,558-563; full_duplex_metrics.md:120 | Load VAD only when interruption scoring needs it. The output records package version/configuration but no model hash; qualify same-byte reruns by fixed dependencies/model/runtime and pin those artifacts. |
| "Same official settings" does not establish identical timestamp output. | official_eval_backchannel.py:41-45; unified_v10.py:88-97 | Official requests return_seconds=True; unified converts sample indices itself. Current Silero rounds second-valued timestamps to one decimal place, so distinguish shared detector settings from identical boundary precision. |
| The claim that all 87 receive official response latency/rating is unsupported by these aggregates. | final_design.md:15; official_eval_user_interruption.py:96-115 | All samples enter the takeover denominator, but empty transcripts and outputs both shorter than 1 s and <=3 words get TOR=0; only TOR=1 receives latency/rating. Establish the claim from per-sample official outputs or weaken it. |

2.1. Additional upstream interruption defects matter when presenting its numbers as a reference. A failed judge parse retries after appending TOR, potentially duplicating successful-takeover observations; each accepted rating is appended twice, which leaves its mean unchanged but does not create independent evidence; all-TOR-zero inputs reach division by zero for rating/latency.

2.2. Verification scope: pure-function probes were executed; waveform replay and end-to-end score_tree execution were not performed because the attachments contain no WAV/reference tree and the runtime lacks silero_vad and the imported benchmarks package.

3. Backchannel and turn-taking decisions

3.1. Not porting the backchannel scorer is justified; "count dominates timing" is not established. The upstream code confirms unconditional inclusion of every processed <=3-second segment, including segments marked takeover; per-segment overwriting of TOR; and termination at the first >3-second segment, dropping subsequent timing/frequency observations. The normalized histogram defeats a blanket count-dominance argument: multiplying all occupied-bin counts by the same positive factor preserves its shape apart from the 1e-10 smoothing effect. Event placement, duration and coverage can change the distance, but event count is not an independent multiplicative penalty after normalization.

3.2. The no-event value is a separate penalty mislabeled as a distance. SciPy returns the square root of JS divergence; with natural logs its maximum is sqrt(log(2)) = 0.8325546, so the no-event value 1 is outside that distance's range. For no-event fraction p0, the reported average is p0 + (1 - p0) * mean distance; no-event prevalence can dominate, and adding any processed event guarantees a score below the no-event penalty regardless of timing. Report no-event rate/frequency separately from conditional timing quality in any future replacement.

3.3. Do not attribute the removed scorer's null-end crash to this upstream backchannel implementation. The upstream file skips many null-ended words and substitutes the start for other null ends; the removed scorer itself is not attached.

3.4. Keeping turn-taking ASR-only is justified as a scope decision, not as a demonstrated accuracy advantage. The counts imply 5 VAD-only flags, 8 ASR-only flags, and 13/595 = 2.18% detector disagreement. An ASR-or-VAD gate would add 5/595 = 0.84 points overall and up to 2/119 = 1.68 points for one system; replacing ASR with VAD would change one system by -3/119 = -2.52 points. Turn-taking retains pre-E ASR evidence, whereas interruption ASR is cropped at R. Audit all 13 disagreements before claiming detector superiority.

4. Reviewer attacks, ordered

| Priority | First attack | Evidence needed |
|---|---|---|
| 1 | Construct validity: a system can ignore most of the interruption, finish naturally before R, and obtain a valid low-latency response. | Cessation/overlap/restart measurements; matched muted-interruption control; content checks separating continuation from a new answer. |
| 2 | Endogenous selection: excluding 87/200 samples changes the evaluated population, while conditional success remains numerically high. | Paired common-exercise results, exercise-stratum counts, explicit estimands and completion bounds; interruption recordings from additional systems. |
| 3 | Detector validity: stable aggregate sweeps are not ground truth, and "official defaults" do not establish cross-system calibration. | Human-adjudicated S/R boundaries; per-item transition matrices; sensitivity to padding, minimum speech duration and annotation jitter. |
| 4 | Evidence/provenance gaps: aggregates cannot reproduce individual reclassifications. | Reference trees/per-sample rows, pinned detector/model artifacts, boundary tests, ASR-manifest binding and reference-column integration tests. |
| 5 | Statistical overinterpretation: Wilson/bootstrap intervals quantify neither selection uncertainty nor generation/detector error. | Paired effect intervals, repeated captures, clustering, separate presentation of sampling intervals versus worst-case bounds. |
| 6 | Scope inflation and gaming: silence wins pause handling, canned words win response timing, accepted acknowledgments are penalized, and backchannel quality remains unmeasured. | Joint task reporting, semantic controls, claims restricted to timing proxies. |
| 7 | System-versus-model attribution: FIFO playout and protocol-specific buffer clearing affect measured cessation. | Claim delivered-system performance, document buffering/clear semantics. |

## 采纳记录

改动在 sglang-omni#2808 第二个提交 `4c923c58`，Nemotron 重算结果在 `docs/runs/2026-10-14-vadgate/sweep-unified4-final.jsonl`。

- **它同意的**：没打断到的样本当未知、不当失败；附和不移植；轮转保持只用 ASR（它补充说这是范围决定，不是证明了 ASR 更准）；核心比率与延迟实现符合定义。
- **它反对、我改判的**：
  - 每个样本独立记录 S 时刻和 R 时刻的语音状态，没打断到的样本里"打断期间开口并说过 R"的情况不再被吞掉（Nemotron 上 2 个）。
  - "R 时刻还在说话"改为"在 R 之前开始、跨过 R 的语音"，恰好从 R 开始的新回复不算，与轮转对 E 的处理一致；VAD 关掉 30 ms 填充，避免把 R 之后刚开始的回复挪到 R 之前。
  - 新增三项诊断：S 到停下的时长、打断期间说话占比、R 之前重新开口。Nemotron 默认设置下中位 1.09 s、0.371、25/109。重新开口率对最短静音很敏感（0.05 到 0.27），文档写明只作诊断。
  - output.wav 时长必须等于 T；词的结束时间按 [0, T] 与开始时间校验（6709 个真实词无一违反）；VAD 只在有打断样本时加载；记录模型文件哈希；只有官方结果的子集（附和）也打印。
  - 文档措辞：去掉"没打断到任何东西""无回应即静音"；官方打断评测一条改为"一视同仁地打分，R 之后的回复照样进入接管率、延迟和评审"；附和 JSD 一条改为"平均值混合了无附和样本比例与其余样本的时机距离"，删去"距离随附和次数变化"；上下界写明是固定打断时刻协议下的最坏补全。
  - 系统间比较补充报告"两边都被打断到 / 只有一边 / 都没有"的样本数。
- **它反对但我没做的**：
  - 静音打断音频的对照组、人工标注 S/R 边界、逐条听 13 个轮转检测分歧：需要新录制或人工，10-23 talk 前不做，文档写明停下时长不能区分"被打断而停"与"自己说完"。
  - ASR 与 manifest 版本绑定：流程上 reference-asr 对同一棵树只允许跑一次，重新导出会生成新树，不再额外加检查。
  - 改变实验协议（按说话状态触发打断）：属于新数据集设计，talk 之后再说。
