# 用 #2331 评测工具测半双工端点：差距与方案（2026-10-10）

依据：sgl-project/sglang-omni main `cf49615` 的 `benchmarks/duplex/`，以及 lijrjyan/sglang-omni-cascade-private#1（Yuhao，head `8d03145`）的 `sglang_omni/serve/realtime/`。

## 结论

现有评测工具不能原样驱动半双工端点。推荐方案 B：评测工具增加一种协议模式，直接讲半双工会话使用的旧版 realtime 协议，约 300 行代码加 150 行测试，服务端不改，也适用于之后放在同一协议后面的级联适配器。

## 差距

- 评测客户端讲原生会话协议：结束时发 `sglang.input_audio.end` 并等待 `drained`，再 `session.close`；校验器要求每段输入都有 `accepted`、覆盖输入的 `sglang.unit.done`，以及 `session.updated` 中声明的原生能力。
- 半双工会话由 `LegacyRealtimeFacade` 提供，只接受 update、append、clear、`response.cancel` 与 truncate；对 `end` 和 `session.close` 返回 `not_supported`；不发 accepted、ended、drained；音频事件名为 `response.audio.delta`，24 kHz 但协议中不声明采样率；只认旧字段 `modalities`（默认只出文字），评测工具发的 `output_modalities` 被忽略。
- 原样运行的结果：没有音频，每个会话跑满超时后失败。更糟的是导出不看校验结果，会产出"合格"但全静音的 `output.wav`。

## 方案

- **A（改服务端）**：让半双工会话接受原生扩展事件。最小改动约 25 行，但事件名、采样率、校验器仍不兼容；彻底的做法是让带特定参数的客户端走 `SharedRealtimeSession`，服务端约 50 行加测试，评测侧约 150 行，并且要在别人的 PR 里加第二条协议路径。
- **B（改评测工具，推荐）**：会话开始发 `session.update`（`modalities: ["text","audio"]` 与 `turn_detection`）并核对回显；保留输入的 `sglang.seq/t_start_ms`；输入结束 1 秒后发一次无操作的 `session.update` 作存活探测，收到回执即关闭连接；新增一条半双工校验分支；重建音频时识别 `response.audio.delta`、静音会话补零、在 `output_audio_buffer.cleared` 或 `speech_started` 处截断播放；profile 增加协议字段，采样率取自 profile。

半双工端点的 profile：`native_unit_ms=20`、`output_sample_rate=24000`、`stop_requires_eos=False`、`continuous_output=False`。

## 判轮参数扫描

- 每个样本是一个新连接，`turn_detection` 可按会话设置，无需重启服务。
- `server_vad`：可调 `silence_duration_ms`（默认 500）、`threshold`（Silero 语音概率，不是 Smart Turn 阈值）、`prefix_padding_ms`。
- `semantic_vad`：Smart Turn 阈值只能通过 `eagerness` 三档预设调（low/medium/high 对应置信度 0.92/0.88/0.80）；连续扫描需要服务端约 15 行改动。

## 发现的服务端问题（应告知 Yuhao）

- `semantic_vad` 与 `silence_duration_ms` 同时设置会抛出 ValueError，落到通用异常处理里直接断开会话。
- 单次用户发言超过 30 秒会触发致命的缓冲区溢出；FDB v1.0 的 Candor 轮转最长输入 94 秒，静音阈值调大时更容易触发。
- 未加载 Smart Turn 时，`semantic_vad` 会静默退化为 `server_vad`，需在 `session.updated` 中核对实际类型。

## 第一个实验

Qwen3-Omni（`SGLANG_OMNI_QWEN_REALTIME_BACKEND=runtime`），FDB v1.0 `candor_pause_handling`（216）与 `candor_turn_taking`（119），先每类 20 条试跑再全量；6 组：`server_vad` 静音 500/800/1200 ms，`semantic_vad` eagerness low/medium/high。指标为停顿接管率（低好）对轮转接管率（高好）与延迟，画权衡曲线。
