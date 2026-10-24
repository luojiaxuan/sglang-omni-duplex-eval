# 外审：合并两套 FDB v1.0 自定义评分（2026-10-14）

- 对象：sgl-project/sglang-omni#2808，把 #2331 的 VAD 门控并入 `unified-score`，删除 `transcribe`/`score`。
- 渠道：ChatGPT 网页在 Claude in Chrome 里处于登出状态（01:05 PT），我不能代登录，未能外审。替代做法是起一个独立的对抗式审稿子代理，读同一组附件。**待补审**：ChatGPT 恢复登录后，用同一组材料补一次 Pro 档外审，结论仍可推翻下面的决定。
- 附件：`docs/runs/2026-10-14-vadgate/design_note.md`（审前判断与数据）、`unified_v10.py`、`v10_scoring.py`、`full_duplex_metrics.md`、官方 `eval_backchannel.py`、`sweep-single-segment-onnx.jsonl`。
- 数据：Nemotron 原生全双工 v1.0 录制（HF `gavinlaw/sglang-omni-fdb-native-runs` rev `0cb3e190`，`20261009-nemotron-voicechat/ref-v10.tar`），打断子集 200 条；轮转对照用同一数据集的 Qwen3-Omni 半双工四个判轮配置（`20261010-turn-sweep-qwen3omni/score.tar`）。脚本在 `code/vadgate_20261014/`。

## 审前判断（摘要，全文见 design_note.md）

1. 打断：VAD 判"没测到打断"（S 时刻模型不在说话）排除出分母并报 `exercised_rate`；"一直没停"（一段语音覆盖 [S, R]）算失败。
2. 轮转不加 VAD。
3. 附和移植 #2331 的规则，没有附和的样本 JSD 记 1。
4. VAD 用 Silero 默认参数，与官方附和评测一致。
5. 删除 v10_scoring / v10_evaluation 与两个子命令。

## 审稿意见（子代理原文，英文）

见本文件末尾附录。

## 采纳记录

- **它同意的**：轮转不加 VAD；"一直没停"应算失败而不是排除；官方附和评测的两个 bug 判断正确。
- **它反对、我改判的**：
  - "没测到打断"不再静默退出：仍不进分母，但在 `selected_bounds` 里和不合格样本一样当未知结果。全程不开口的系统上下界是 [0, 1]，一眼可见没测到。
  - "一直没停"改为"R 时刻还在说话"（`speaking_at_end`）：原来要求一整段语音不断，任何超过 100 ms 的停顿都会漏掉。Nemotron 上原判法 0 个，新判法 4 个。
  - 附和不移植：移植版遇到空结束时间的词会抛 TypeError，JSD=1 超出距离上限 0.83，且该距离主要随附和次数变化。附和只保留官方结果，文档列出官方评测的已知问题。
  - VAD 改用 `load_silero_vad()` 默认模型（与官方附和评测同款），不用 ONNX；`unified.json` 记录版本与参数；打断样本的 `output.wav` 按 manifest 校验哈希。
  - 播放时间线：核实导出器对旧版 realtime 协议会在 `output_audio_buffer.cleared` 时截断排队音频；原生全双工协议没有清空事件，文档写明打断结果描述的是系统按交付状态的表现。
  - 定义版本升到 `fdb-v1.0-unified-4`，文档补"官方打断评测把没打断到的样本也算作打断回应"一条。
- **它反对但我没做的**：
  - 停止延迟曲线、静音打断音频做正对照、逐条听 13 个检测分歧样本：需要新录制或人工听审，超出这个 PR 的范围，留作后续。
  - 在 main 上打 tag 保存旧评分：改为在 PR 里写明旧代码所在提交 `e9e016b`，不在公开仓库新建 tag。
  - 全部 5 个系统做打断参数扫描：只有 Nemotron 录了打断子集，做不了。

## Nemotron 打断子集结果（200 条）

| 指标 | unified-3 | unified-4 |
|---|---|---|
| 计入比率的样本 | 200 | 113（被打断到的） |
| 2 秒内回应率 | 0.965 | 0.956，全选上下界 [0.540, 0.975] |
| 无回应率 | 0.010 | 0.000 |
| R 时刻仍在说话 | 无此项 | 4/113 |
| 延迟中位数 | 1.20 s | 1.20 s |

- 87 个"没测到打断"里 83 个是模型已经说完，停在 S 前中位 1.32 s；5 个停顿短于 0.3 s，可能是句间停顿被误判。
- 打断时长 R − S：最短 1.7 s，中位 3.42 s。
- 参数扫描（阈值 0.3/0.5/0.7 × 最短静音 50/100/300/500 ms）：`not_exercised` 84–91，`speaking_at_end` 4–5，2 秒回应率 0.946–0.957，延迟中位 1.12–1.20 s。
- 轮转 VAD 对照（5 个系统各 119 条）：只有 VAD 判到提前开口的 1/2/0/1/1 条，只有 ASR 判到的 0/4/3/0/1 条。

## 决策日志（替 luojiaxuan 做的默认决定）

1. **附和不移植**
   - 问题：计划里说附和沿用 #2331 的 VAD 版本，要不要照做？
   - 默认：不移植，附和只用官方结果并写明已知问题。
   - 理由：移植版有崩溃路径，JSD=1 的约定站不住，修好需要重新定义和验证。
   - 回滚：后续单独开 PR，按审稿意见重新定义附和指标。
   - 外审：子代理认为 JSD=1 属于阻断性问题；ChatGPT 待补审。
2. **PR 不等 #2794 合入就开**
   - 问题：计划是 #2794 先合，再开合并评分的 PR。
   - 默认：现在就开，对 main，不叠分支。
   - 理由：附和不移植后，unified-score 的命令行不变，和 #2794 自己的提交没有文件冲突。
   - 回滚：合并顺序仍可让 #2794 先合；#2808 只在评审通过后合。
   - 外审：未涉及。
3. **打断判定用 R 时刻的状态**
   - 问题：沿用 #2331 的"整段覆盖"，还是改判？
   - 默认：改为 R 时刻是否在说话。
   - 理由：不引入新参数，能抓到中途停顿后继续说的情况；数据上 0 个对 4 个。
   - 回滚：`interruption_sample` 里一个条件，可改回。
   - 外审：子代理建议用 [R − w, R] 窗口；我取 w = 0，避免新增一个要扫描的超参。
4. **没测到打断的样本计入上下界**
   - 问题：直接排除，还是当未知结果？
   - 默认：当未知结果。
   - 理由：是否被打断到取决于系统，直接排除可以被钻空子。
   - 回滚：`subset_metrics` 里一个参数。
   - 外审：子代理建议，采纳。

## 附录：子代理审稿原文

Several parts of the proposal don't hold up. Five findings are BLOCKING: the headline that is conditional on exercised samples, the single-segment `talked_through` definition, the JSD=1 imputation, a port that will crash on null-end words, and the definitions version that isn't bumped. A sixth BLOCKING item is a check you need to run: whether the FIFO playout honors a stop signal. I checked the line-by-line claims about the official evaluator. Two of the three hold, the third holds only partly, and the official evaluator has further bugs the note doesn't list.

**Q1. `not_exercised`**

1. **BLOCKING.** Excluding `not_exercised` from the headline can be gamed and biases which samples get compared (design_note.md:12, :19). For Nemotron 87/200 samples were not exercised, and 83 of those were because it had already finished talking. Whether a sample is exercised depends on how long the system talks, how fast it speaks and how late it starts answering. So rates conditional on exercised samples compare different sample sets across systems: a silent system gets n=0, which shows as "n/a", not as a failure; a terse system is scored only on its few longest answers. **Recommendation:** make `not_exercised` an outcome in a full partition over eligible samples: {`not_exercised`, `not_yielded`, `yielded_no_response`, `response`}. The headline is a share of eligible samples, with bounds `[handled/eligible, (handled + not_exercised)/eligible]`, the same construction `selected_bounds` already uses for ineligible samples. A silent system then shows bounds of [0, 1], visibly unmeasured, and a terse system's lower bound is penalized. Keep the conditional rates as secondary metrics, always printed next to `exercised_rate` and n.
2. **ADVISORY.** Split `not_exercised` into `finished_before_onset` (83) and `silent_before_onset` (4). Report the low end of the gap: a gap of a few hundred ms is a pause between sentences, not a finished answer, and the check at the single instant S labels those `not_exercised`.
3. **ADVISORY.** Pairing on "exercised in both" gives a sample set that changes with every pair, so comparisons aren't transitive. Pair on all eligible samples using the partition outcome; keep exercised-in-both as a secondary view.

**Q2. `talked_through`**

4. **BLOCKING.** Counting it as a failure is correct, but the single-segment definition misses most real talking-through. With min_silence at 100 ms, any pause of 100 ms or more between phrases splits the segment, so a model that ignores the user and keeps reading its answer is labeled exercised and its continuation after R is scored as a near-zero-latency response. The sweep shows the label depends on pause length (0 to 3 as min_silence goes from 100 to 500 ms). **Recommendation:** define the outcome by the model's state at R: "yielded" means no model VAD speech in [R − w, R]; report stop latency from S as a curve with infinity for "not yielded"; sweep w; add a positive control with the interruption audio muted; listen to the samples that flip at 500 ms.
5. **BLOCKING (check needed).** The FIFO playout never flushes. A system that streams ahead of real time and then cancels still "plays" its queued audio past R, so the outcome measures buffer depth, not barge-in. Confirm the client honors whatever stop or clear signal the protocol offers, or document that the outcome belongs to the system plus the client.
6. **ADVISORY.** Report the distribution of R − S.

**Q3. Turn-taking**

7. **ADVISORY.** Agree with dropping VAD here. The ASR-only early starts (0/4/3/0/1) are the error budget of the rule being kept. Listen to the 13 disagreement samples, put the disagreement rate in the docs as a measurement-error bound, and state the principle: ASR word onsets wherever the transcript covers the region, VAD only where it doesn't.

**Q4. Backchannel**

8. **ADVISORY.** Both bug claims are correct. Missed: a `break` on the first segment over 3 s drops later segments from frequency and JSD; TOR is initialized inside the `else` branch, so a missing `output.json` leaves a stale TOR; frequency is divided by the output wav length; the "JSD" is SciPy's JS distance with natural log, maximum sqrt(ln 2) = 0.8326, so 1 is out of range; null-end words are dropped from the word count.
9. **BLOCKING (port).** Thresholds match the official rule, but word counting differs (open overlap vs the official inclusive end; null ends), the port raises TypeError on a null end, and clipping at T can turn a cut-off takeover into a backchannel.
10. **BLOCKING.** JSD=1 for samples without backchannels is not defensible: it exceeds the 0.8326 maximum, mixes presence with timing, and the distance is driven by count, not timing (one backchannel at the human peak 0.805, ten random 0.740, forty random 0.611). Report presence rate separately and compute timing only over samples with backchannels against a count-matched random baseline.
11. **ADVISORY.** Any-segment takeover grows with sample length; VAD merges close backchannels; padding adds 60 ms; a correct reply after the monologue counts as a takeover.
12. **ADVISORY.** Pooled backchannels per minute departs from the official per-sample mean; label and justify the denominator.

**Q5. What a reviewer would attack first**

13. **BLOCKING.** unified-3 scores 85 of Nemotron's 200 interruption samples as responses when they were replies to a new turn. Bump `DEFINITIONS_VERSION`, mark reported unified-3 interruption numbers as superseded, and rewrite the doc (line 3 says no model is needed).
14. **ADVISORY.** "Same as the official evaluator" holds only for the parameter values: the official uses the default `load_silero_vad()` model with torchaudio resampling; v10 uses ONNX and `resample_poly`. Record version, model flavor, config and the `output.wav` sha256, and hash-check `output.wav`.
15. **ADVISORY.** The sweep covers one system and counts only; run it on all systems and report headline metrics and ranking per cell.
16. **ADVISORY.** Present `exercised_rate` as a property of benchmark and system together, not as a quality score.
17. **ADVISORY.** Tag main before deleting `v10_scoring.py` and `v10_evaluation.py`.
