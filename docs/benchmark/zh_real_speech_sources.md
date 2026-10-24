# 中文真实语音评测集:数据来源

结论:不自录。以 SmoothConv 为主来源,按 FDB v1 的规则切接话、停顿与附和样本;LiveKit eot-bench 中文子集作第二来源;同一批转写按 FDB-zh 流程重新合成,做真人与合成的配对比较。估计 3 至 4 人日(切分脚本 1–2,人工复核约 1,配对合成约 0.5)。调研时间 2026-10-04 PT。

| 来源 | 类型 | 规模 | 声道 / 标注 | 许可 | 用途 |
|---|---|---|---|---|---|
| [SmoothConv](https://huggingface.co/datasets/qualialabsAI/SmoothConv) | 真人自发对话(闲聊与辅导) | 100.5 h,2503 段 | 2–4 声道,`channelIndex` 对应说话人;段级时间戳,人工标注 `turn` = complete / incomplete / backchannel / wait | CC BY-NC 4.0 | 主来源,三类任务都能切;闲聊双声道子集约 14 GB |
| [LiveKit eot-bench](https://huggingface.co/datasets/livekit/eot-bench-data) 中文子集 | 真人对语音助手说话 | 344 条 | 仅用户侧;每段 ≥100 ms 静默标 `hold` 或 `eot`,带 ASR 词级时间戳 | CC BY 4.0 | 停顿与接话的第二来源(人机任务型) |
| [MagicData-RAMC](https://openslr.org/123/) | 真人电话对话 | 180 h | 双声道,句段级时间戳 | CC BY-NC-ND 4.0 加 Magic Data 许可,切片不可再分发 | 仅内部第三验证集 |
| [AliMeeting](https://www.openslr.org/119) | 真人会议,2–4 人 | 119 h | 近场耳麦逐人分文件,TextGrid 段级 | CC BY-SA 4.0 | 多人场景备选 |

已排除:Easy Turn / FastTurn 测试集(1–3 s 单句片段,只能做判轮分类,做不了 FDB 式停顿);pipecat smart-turn v3.2 测试集中文 929 条全部合成;HumDial、RealTalk-CN 为脚本演绎;WenetSpeech、Emilia、KeSpeech 为单声道媒体或朗读;HKUST、CallHome 需 LDC 付费。

FDB v1 的切分规则(论文 §III;仓库无构造脚本):
- 停顿:单人说话区间内 0.4–1.0 s 的轮内停顿,轮长 ≥5 s,停顿前后无附和;
- 接话:相邻两轮间隔 <0.4 s,无重叠,每轮 >4 s,非附和;输入末尾补 5 s 静音;
- 自动筛选后逐条对照双声道人工复核。

注意:SmoothConv 的 `turn` 标签只覆盖部分片段,其余需过滤;辅导子集含儿童说话人;FDB 的附和判定"≤3 词"用于中文时要改为按字或分词计。
