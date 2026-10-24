# 外审: talk 结果汇总 (2026-10-16)

被审材料: talk 结果汇总 (只存在 luojiaxuan 本地, 不进仓库; 数字都来自下面的 JSON 与运行记录), 三份合并结果 JSON, `benchmarks/duplex/unified_v10.py` 与 `docs/developer_reference/full_duplex_metrics.md` (sglang-omni main `85d4219`).

## 发审前我的判断

1. 结论 1 (官方 v1.0 把失败算成功) 站得住: 打断题官方只看转写的词, 我们用输出音频的 VAD 判断模型是否停下, 41% 到用户说完还在说是直接观测. 最可能被攻击的是"统一口径是自己定义的": 35 条 not_exercised 被移出分母; VAD 参数在 MiniCPM-o 上没扫.
2. 结论 2 (1 秒单元结构) 是推断, 证据是 1 秒内与 2 秒内回应率的跳变和两个数据集的停下时延一致. 更硬的证据应该是回应时延分布在 1 秒整数倍附近聚集, 目前没画.
3. 结论 3 依赖 Qwen 判分, 没量和 GPT-4o 的一致率, 应在 talk 里标明判分模型.
4. 结论 4 只有 1 到 8 路, 上限扫描在做; 客户端与服务端同机.
5. 单次生成是共同的弱点, 置信区间只含样本抽样.

## 外审全文 (ChatGPT 网页临时会话, 最新旗舰模型 Pro 档, 思考 14m34s, 10-15 19:40 PT 取回)

附件: 汇总 md, `full_duplex_metrics.md`, `unified_v10.py`, `minicpmo-v10-merged.json`, `minicpmo-v15-merged.json`, `minicpmo-serving-2843.json`. 页面里的引用角标在取回文本中只剩文件名, 原样保留.

````text
1. Claim audit and replacement wording
1.1 Official v1.0 scoring counts failures as successes — PARTIALLY SUPPORTED

Strongest attack: The comparison changes both the criterion and denominator: transcript-based takeover is not successful interruption handling; unified interruption outcomes condition on detected speech at onset. Aggregate disagreement does not identify which official takeovers were failures under the unified rule, much less establish perceptual ground truth. The supplied specification documents the blind spot, but the original evaluator and sample-level cross-tabulation are absent. [full_duplex_metrics]

Additional attack: speaking_at_end includes stopping and restarting before the user finishes; it does not necessarily mean uninterrupted speech throughout the interruption. stop_s measures the end of the VAD segment covering onset, not an interruption-caused stop. Delivered audio also includes previously queued native output. [unified_v10] [full_duplex_metrics]

Replacement:
The reference evaluator reports takeover 0.9358 and rating 4.30. Under the unified delivered-audio metric, 165/200 samples contain detected model speech at interruption onset; 68/165, or 41.2% [95% CI 34.0–48.8%], contain speech crossing the interruption end. The segment covering interruption onset ends after a median 2.131 s [1.779, 2.280]; detected speech occupies 73.6% of pooled interruption time. High reference takeover therefore coexists with substantial output overlap; it should not be interpreted as successful stopping.
Keys: subsets.synthetic_user_interruption.{official,metrics.exercised_rate,metrics.speaking_at_end_rate,metrics.stop_latency_s,metrics.speech_s_per_interruption_s}. [minicpmo-v10-merged]
Retain the 35 non-exercised samples explicitly: speaking_at_end_rate.selected_bounds=[0.340,0.515] describes worst-case completion over all 200 selected samples, not a confidence interval. [minicpmo-v10-merged] [full_duplex_metrics]

1.2 The 1 s processing unit explains latency — NUMBERS SUPPORTED; CAUSAL ATTRIBUTION UNSUPPORTED

Strongest attack: Three response thresholds do not demonstrate one-second periodicity or identify its cause. The attachments do not separate boundary waiting, model decisions, processing, queued-audio playback, and ASR timing; the metric documentation explicitly excludes acoustic latency. [minicpmo-v10-merged] [full_duplex_metrics]

Cross-version attack: v1.0's 2.131 s is a median over 165 onset-exercised samples; v1.5's 2.247 s is a pooled mean over 201 extracted stop intervals from 200 samples, five of which have no stop interval. Numerically similar values are not a same-estimand replication. The v1.5 median is 2.204 s, but changing mean to median alone does not harmonize eligibility or interval extraction. [minicpmo-v10-merged] [minicpmo-v15-merged]

Replacement:
With the configured 1 s processing unit, valid turn-taking responses occurred within 1/2 s in 7/119 (5.9%)/72/119 (60.5%) samples; valid interruption responses occurred within 1/2 s in 2/165 (1.2%)/57/165 (34.5%) exercised samples. These are observed timing distributions, not an estimate of the processing-unit effect. The v1.0 and v1.5 stop summaries use different estimands.
Keys: subsets.{candor_turn_taking,synthetic_user_interruption}.metrics.response_rate_{1,2}s.

1.3 Handles backchannels but responds to unaddressed speech — SUPPORTED AS JUDGE-LABEL FREQUENCIES

Strongest attack: The disclosed substitute judge was not calibrated against the official judge on these recordings. C_RESPOND is an assigned behavior label, not direct evidence that the model believed speech was addressed to it; C_RESUME does not establish uninterrupted continuation or overall semantic correctness. Judge provenance is stated in the Markdown, not retained as judge configuration in the merged label records.

Replacement:
Under the reported self-hosted Qwen judge, backchannel cases received C_RESUME in 96/98 samples, 98.0% [bootstrap 95% CI 94.9–100%]. Cases annotated talking_to_other and background_speech received C_RESPOND in 38/100 [29–48%] and 19/100 [12–27%], respectively. These are judge-assigned behavior rates, without measured judge agreement on this capture.
Keys: categories.user_backchannel.labels.C_RESUME; categories.{talking_to_other,background_speech}.labels.C_RESPOND.

1.4 One H200 serves eight sessions with zero missed units — SUPPORTED FOR THE TESTED WORKLOAD

Strongest attack: Zero missed processing units does not mean glitch-free playback. At concurrency eight, playback_reserve_s=0.08, replies_with_underrun=21/35=60%, and underrun_s=2.189; required startup buffer p90 is 251 ms. These results do not establish sustained capacity or zero future misses. [minicpmo-serving-2843]

Replacement:
On the reported single-H200, local-loopback test, target concurrency eight achieved mean open sessions 7.788 across 32 sessions. All 432 expected units were recorded, with zero misses; unit lag p99 was 604 ms and maximum 619 ms. Eight is the highest tested passing concurrency, not a measured capacity limit. Playback underruns occurred in 21/35 replies with the configured 80 ms reserve.
Keys: levels[concurrency=8].{mean_open_sessions,sessions,units_expected,units_missed,unit_lag_s,playback_reserve_s,replies_with_underrun}; max_concurrency_meeting_targets=8; capacity_bounded=false.

2. Markdown–JSON numerical audit
- Hard count mismatch: v1.0 "727 samples" and "ICC 55". The JSON records subsets.icc_backchannel.selected=0, eligible=0; summed selected/eligible counts are 137+216+119+200+0=672, not 727. The official ICC values are nevertheless present. Reconcile against the original manifest; do not infer from this merged artifact alone that the 55 cases were never run, because unified scoring explicitly skips backchannel subsets.
- Definition mismatch: "停顿时插话" 0.175/0.310. These match pause_intrusion_rate, which counts ASR word onsets from the first pause start through window end, including after speech resumes. Literal inside-pause onset rates are inside_pause_onset_rate: 6/137=4.4%, 19/216=8.8%. Rename the column to "word onset after first annotated pause start"; do not describe every counted onset as an established premature interruption.
- Denominator mismatch: v1.5 "语义三项全过". Every displayed percentage matches semantic.joint.quality, but this equals accepted / (accepted + failed), excluding unresolved judgments, not accepted/all pairs; use the corrected denominator table below.
- Timing-denominator omission, not scalar mismatch. v1.5 overall stop/response means summarize 493/721 intervals, not 498 equally weighted pair-level latencies; 13/4 samples have no corresponding interval. zero_interval_samples is a count of samples lacking intervals, not a zero-second latency assignment. Label the means "pooled extracted-interval mean, sample-bootstrap CI."
- Aggregation anomaly, not Markdown rounding error. subsets.synthetic_user_interruption.official.takeover_rate × selected = 0.9357692307692308 × 200 = 187.153846…; this cannot be a simple micro-average of 200 binary takeover flags. Recover the aggregation rule and underlying counts; macro/shard weighting is a possibility, not an established explanation.
- Unsupported numerical provenance: client/server median difference "1–2 ms". The claim appears in the Markdown, but the serving JSON supplies client summaries without matched server timing or reconciliation-difference fields. Treat this number as unverified from the attachments, not contradicted.
- Rating provenance omission. The 4.30 scalar matches the JSON, but .official alone does not establish official-judge provenance. The supplied renderer explicitly labels substitute-judge results "reference … not official"; retain that distinction when recovering the original judge metadata.
- v1.5 semantic denominator correction: retain quality only with resolved coverage; alternatively report known accepted/all-selected plus unresolved_bounds, which are worst-case completions, not 95% confidence intervals.

| Category | Markdown = resolved-only pass rate | Resolved coverage | Known accepted / all selected | Unresolved-completion bounds |
| All | 224/418 = 53.6% | 83.9% | 224/498 = 45.0% | 45.0–61.0% |
| User interruption | 83/153 = 54.2% | 76.5% | 83/200 = 41.5% | 41.5–65.0% |
| User backchannel | 80/82 = 97.6% | 83.7% | 80/98 = 81.6% | 81.6–98.0% |
| Talking to other | 22/91 = 24.2% | 91.0% | 22/100 = 22.0% | 22.0–31.0% |
| Background speech | 39/92 = 42.4% | 92.0% | 39/100 = 39.0% | 39.0–47.0% |

The remaining summary-table numerical fields agree with their corresponding JSON scalars at the displayed precision; the qualifications above concern counts, denominators, definitions, and provenance.
full_duplex_metrics.md's 39 clamped latencies, 87 non-exercised samples, and 85–95 non-exercised VAD-sweep range describe example captures, not additional MiniCPM measurements; the summary explicitly says the VAD sweep used another native system. Do not import those numbers as MiniCPM validation.

3. Cheapest strengthening analyses
- 0, aggregate-only, no GPU: Report all-denominator response_latency_s: turn-taking median 1.82 s [1.69,1.98], 98/119 responses, p90 not reached; interruption median 2.40 s [2.24,3.12], 96/165 responses, p90 not reached. Strengthens the descriptive latency argument without responder-only averaging; "not reached" follows the scorer's failure-at-infinity convention.
- 1, highest-value claim-1 analysis, CPU join: Recover original official per-sample results, unified-samples.jsonl, and aggregation code. Verify sample IDs and manifest/ASR hashes; cross-tabulate official takeover × {not_exercised, speaking_at_end, response, no_response}, with rating summaries per cell. Reconstruct micro counts and distinguish them from shard averages. Split endpoint overlap into continuous initial-segment overlap versus stop-and-restart using stop_s, interruption_s, and endpoint flags. Establishes an actual official-takeover/unified-failure intersection; resolves the noninteger takeover-count anomaly and the ambiguity in "still speaking."
- 2, validate claim 1's failure label, CPU + listening: Reuse the 200 MiniCPM recordings and cached ASR. Run threshold {0.3,0.5,0.7} × minimum silence {50,100,250,500} ms: 12 configurations, retaining minimum speech 250 ms and padding 0. Report exercised denominators, endpoint rates, stop medians, overlap ratios, and sample-level classification changes; inspect S/R-boundary sensitivity. Blind-audit a stratified 20–30 clips from disagreement and boundary cells; do not present the purposive audit as a population error-rate estimate.
- 3, highest-value claim-2 analysis, CPU traces: Recover per-sample reference times and unit-send, result-receive, audio-arrival, and playout timestamps. Plot latency against residual time to the next unit boundary, w = next_boundary(reference) − reference. Decompose boundary waiting, processing/delivery, and queued playout per sample. Test phase association. Keep turn-taking reference E, interruption response reference R, and stop reference S distinct.
- 4, make the cross-version comparison meaningful, CPU VAD: Re-score existing v1.5 interruption audio using the same onset eligibility, VAD settings, S-to-initial-segment-end definition, and median statistic as v1.0. No new ASR is needed.
Retain causal wording only after a matched timing intervention (randomized input-phase offsets or a unit-size ablation) with fresh generation; retain "stops because of the interruption" only after an interruption-muted matched control.
````

## 采纳情况

**它同意的**: 结论 3 (作为判分标签频率) 和结论 4 (作为测过的负载) 的数字都对得上 JSON; 汇总表其余数字与 JSON 一致.

**它反对, 我改判的**:
1. 结论 2 的因果说法. 它指出三个阈值的回应率不能证明 1 秒周期. 我在发审时就怀疑这一点, 随后做了它建议的相位检验 (`code/fdb_main_20261014/unit_phase.py`, 结果 `docs/runs/fdb-main-20261014/minicpmo-unit-phase.txt`): 389 次开口在 1 秒网格上的相位基本均匀 (Rayleigh p = 0.21), 轮转时延与"轮次结束点到下一个单元边界的距离"的相关是 -0.16, 不是单元对齐会给出的正相关. 结论 2 改为描述性, 不归因.
2. v1.0 停下中位 2.13 s 与 v1.5 停下均值 2.25 s 口径不同 (样本资格, 区间提取, 统计量都不一样), 不再说"两个数据集互相印证".
3. "停顿时插话"改名为"首个停顿后开口", 并补上只算停顿内开口的比例 (0.044 / 0.088).
4. v1.5 语义三项全过只算判出结果的样本, 补上覆盖率和"没判出的全算失败"时的 45.0%.
5. 结论 1 措辞改为"高接管率与大量重叠说话同时存在", 补上 35 条未被打断样本的最坏/最好补齐区间 [0.340, 0.515], 并说明"还在说"包括停下后重新开口.
6. 官方打断接管率乘 200 不是整数: 核实是 8 片中有 1 片的判分重试让官方脚本多记了一条 (该片 22/26), 实际是 187 或 188 条, 汇总里改写为"约 0.94"并说明.

**它反对, 我坚持的**:
1. "ICC 727 与 JSON 的 672 不符": 不是错. 统一评分不打 ICC 附和子集, 所以合并 JSON 里它的 selected 为 0; 官方口径的 ICC 55 条在各片 `summary.json` 里都有 (evaluated 合计 55). 汇总表加了一句说明.
2. "服务端与客户端中位差 1 到 2 ms 无出处": 出处是 10-15 的对账, 记录在 `2026-10-14-fdb-main-native.md` 的"用客户端口径重算"一节, 只是没作为附件发给它.

**暂不做的建议**: 官方与统一口径的逐样本交叉表 (需要从 HF 取回输出音频重算统一口径的逐样本行) 和 MiniCPM-o 上的 VAD 参数扫描, 都只要 CPU, 排在服务表之后, talk 前有空再补.
