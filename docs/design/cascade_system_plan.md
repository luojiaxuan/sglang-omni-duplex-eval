# 级联全双工系统实现计划

状态：待实现。目标是交付可持续接收语音、流式回复、允许用户打断并继续对话的级联系统；首版同时验收 Qwen3-TTS 和含 DiT 解码的 CosyVoice3。

## 工作边界

| 工作 | 负责 chat | 交付 |
| --- | --- | --- |
| 级联系统 | 当前 chat | Graph 配置、Session、模型接入、真实取消、播放确认和功能验收 |
| Benchmark | 独立 chat | 数据、小回归、指标、参数扫描和正式评测 |

benchmark 的被测对象是任意 `/v1/realtime` 端点，只通过标准 realtime 协议驱动测试，SGLang-Omni 是默认 provider；系统侧的事件记录只用于诊断。判轮参数选择、数据切分和性能排名由 benchmark 负责。系统侧保留必要的功能检查。

## 已核验的基础

- 现有 `benchmarks/cascade_replay/replay.py` 已串起判轮、LLM 和 TTS，但打断仅设置 `cut_at`，未取消模型请求；历史也未按播放进度提交。
- `serve/realtime/manager.py` 已管理会话；`session.py` 已有 VAD、响应取消和迟到输出过滤；`runtime.py` 管理持续输入与输出。先复用这些能力，补齐级联所需的控制路径。
- `session.py` 已处理 `conversation.item.truncate`，但会把被截断的回复整条从历史中删除，不使用 `audio_end_ms`。
- `SessionRuntime` 当前只声明 native interaction，不能直接把级联适配器挂上去并宣称已支持打断；需要在实现时明确级联能力协商和控制入口。
- CosyVoice3 已有 `FunCosyVoice3StreamingVocoderScheduler`、`PackedDiT` 和 Flow + HiFT 分块解码。共享 streaming vocoder 已有按请求清理状态和丢弃迟到块的路径。真实服务端取消是否贯穿整个级联仍需验收。

## 最小结构

持续麦克风输入分别进入 ASR 和 VAD／判轮节点。轮次提交后，final transcript → LLM → 文本分段 → TTS → 播放。VAD 的打断事件通过 Session 路由到当前回复的 LLM、TTS 和播放端。

- Graph 只声明节点、数据边、控制目标和模型／服务配置。ASR、VAD、LLM、TTS 都是同等节点；不增加独立 plugin 等级。
- Session 持有对话历史、当前回复身份和请求归属。节点使用已有流式、生成和 abort 能力，不另建一套推理调度器。
- 每个回复使用唯一 `response_id`，每段 TTS 使用 `segment_id`，音频块带序号、采样率和样本偏移。LLM token、TTS token、mel frame、播放样本数分别由对应层管理。
- 每段 TTS 音频生成完成后，旁路送入 word aligner 做强制对齐（文字已知），得到段内各词的样本偏移；对齐不阻塞音频下发。生成快于播放，被播放或被打断时对齐结果通常已就绪。
- 首版允许独立 ASR、LLM、TTS 服务；一个配置统一连接与启动，模型／device 放置显式指定。

## 实现顺序

| 阶段 | 实现 | 验收 |
| --- | --- | --- |
| 1. 跑通级联 | 接入现有 Session 生命周期和最小 Graph 配置。使用现有 ASR、Qwen2.5-7B-Instruct、Qwen3-TTS；消费 final transcript，LLM 文本分段送 TTS，持续接收麦克风输入。 | 一个配置启动；中英文各完成连续两轮；正常结束、关闭和断开连接均能清理本会话请求。 |
| 2. 真实打断 | 打断时先使当前回复失效并通知播放端清空待播音频，再取消 LLM 和该回复的 TTS 请求。清除未提交文本和音频，按回复身份丢弃迟到输出。 | 首音频前和播放中均能打断；旧回复不再进入播放队列；下一轮正常；两个 Session 互不影响。 |
| 3. DiT TTS | 将同一图的 TTS 换成 Fun-CosyVoice3，复用其现有流式 Flow + HiFT 解码，固定参考音频及转写。 | Qwen3-TTS 与 CosyVoice3 使用同一 Session、打断和播放路径；CosyVoice3 覆盖首个解码 hop、后续 hop 和 final flush 期间的取消；旧请求状态释放后下一轮可运行。 |
| 4. 播放确认与历史 | 播放确认采用标准的 `conversation.item.truncate`，不新增私有字段：客户端在打断时发送该回复的 `item_id` 与已播放到的 `audio_end_ms`，未收到 truncate 的回复视为完整播放。Session 先按各文本段的样本偏移定位到段，再按 word aligner 给出的段内词级偏移定位到词，只提交已播放的词，未播放的部分不写入历史；当前段尚未生成完就被打断时退化为按段截断。现有的整条删除改为按词保留。 | 已生成但未播放的文本不进入下一轮；指向过期回复的 truncate 不能修改新回复；两种 TTS 都能在打断后继续对话；同一客户端测试其他 `/v1/realtime` 端点时无需改动；词级截断位置与实际播放位置的偏差可由 benchmark 的转写时间戳校验。 |

ASR 首版只要求 final transcript，输入仍持续接收。复用当前能运行的 ASR 服务，不把接入新流式 ASR 模型作为整个系统的前置条件。VAD／判轮使用显式配置，系统实现不承担选阈值工作。

每个阶段形成一个可独立运行、检查和提交的版本；DiT 是首版必验项，不只保留接口声明。

## DiT 支持的具体含义

CosyVoice3 的文本到 speech token 部分是 AR，speech token 到 mel 的后段使用 DiT + flow matching，再由 HiFT 生成波形。因此它能实际检验同一系统是否容纳不同计算模式。F5-TTS 是另一种 DiT／flow-matching TTS；当前仓库未找到其接入实现，本轮以已有 CosyVoice3 为验收对象。

TTS 节点对外接收文本段、输出音频块，允许块长不固定，也允许一个文本段完成后才输出。内部是否逐 token、按 hop 或整段求解，不改变 Session 控制契约；首版统一采用文本分段输入，不假设所有 TTS 都支持可修改的文本前缀。

打断后立即屏蔽旧音频，在模型支持的取消边界停止后续计算并释放本请求状态。DiT 当前执行中的 GPU 操作不承诺即时抢占；验收分别检查播放停止、服务端取消完成和状态释放。取消后停止旧请求的 final flush。

模型状态回退由 adapter 拥有：AR 可管理 KV，DiT／Flow 管理自身条件、前缀与解码状态。通用接口不要求每个节点提供 KV 裁剪。首版历史恢复精度为词：被打断段按 word aligner 的结果保留已播放的词级前缀，以文本提交；模型特定的 KV 回退另行扩展。

## 系统与 benchmark 的接口

沿用现有 realtime 的输入、音频输出、取消和截断协议，不新增私有字段；播放确认即标准的 `conversation.item.truncate`（见第 4 阶段）。benchmark 的指标只取客户端可观测的口径。服务端事件记录覆盖：输入提交、转写完成、回复开始、首音频、音频段结束、打断、播放清空、后端取消完成、回复结束，仅用于 SGLang-Omni 的诊断。

记录带 `session_id`、`response_id`、适用时的 `segment_id` 和明确单位。事件时刻由 Session 的单调时钟记录，模型内部耗时单独注明测量端。音频块带采样率、序号和样本偏移；truncate 以 `item_id` 标识回复、以 `audio_end_ms` 标识已播放位置。首 PCM 产生、网络收到音频和实际播放是不同事件，诊断时分别记录。

功能验收覆盖正常多轮、两 Session 隔离、首音频前取消、播放中打断、DiT hop／flush 取消、迟到块、断开连接和播放历史提交。GPU 验收使用两个真实 TTS；测试替身用于稳定重现取消竞态。全量 benchmark 和性能统计由独立 chat 执行。

## 首版范围与进度

首版交付一套可运行级联、可替换的两个 TTS、真实打断、词级播放历史及一个演示入口。自动 GPU 分配、负载调度优化、推测执行、工具调用、其他模型接入和模型特定的 KV 回退不属于首版。

目前完成代码与模型路径核对；上述四个阶段尚未实现或运行 GPU 验收。计算 home host 与环境在首次部署时确定并记录；模型、参考音频与重产物放在计算主机／HF，Mac 保留代码、配置和轻量记录。

## Source of Truth

- Git：[sglang-omni-cascade-private](https://github.com/lijrjyan/sglang-omni-cascade-private)，系统分支 `luojiaxuan/cascade-system`；代码核验基线 `cascade/p0-replay@4c3010f78507fb346c3ccd529a610687dc91db27`。
- 本计划：`docs/design/cascade_system_plan.md`；模型、配置及功能结果随实现提交到同一系统分支。
- 设计依据：团队飞书 RFC《级联全双工方案设计》(内部文档)。
- DiT 实现依据：[CosyVoice3 cookbook](../cookbook/fun_cosyvoice3.md)、`sglang_omni/models/fun_cosyvoice3/streaming_vocoder.py`、`sglang_omni/scheduling/streaming_vocoder.py`。
- 上游：[CosyVoice Flow](https://github.com/FunAudioLLM/CosyVoice/blob/074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc/cosyvoice/flow/flow.py)、[F5-TTS](https://github.com/SWivid/F5-TTS)。
- Benchmark 基线：[cascade replay](../../benchmarks/cascade_replay/README.md)；HF 日志 `gavinlaw/sglang-omni-cascade-turn-sweep-logs@5f59c747f57d18294383d3aa004802297cf16cd1` 已核验可读取，维护归 benchmark chat。
