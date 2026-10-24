# 三种方案在私有 fork 上的 benchmark (2026-10-19, PT)

目标 (#2 与 benchmark RFC 第 1 节): 原生全双工 (MiniCPM-o)、轮次制 omni (Qwen3-Omni 加 VAD) 和级联 (ASR → LLM → TTS) 三种方案, 在同一个私有 main、同一套客户端和打分下, 报行为准确率 (FDB) 和服务指标 (并发扫描), 其中包括 24 路. 用户 10-19 上午把这项排在听感指标之前.

## 结论

| 维度 | 指标 | MiniCPM-o<br>原生全双工 | Qwen3-Omni<br>轮次制 + VAD | 级联<br>ASR → LLM → TTS |
| --- | --- | ---: | ---: | ---: |
| 行为 | 用户打断时停下回应 ↑ | 56% | **96%** | **96%** |
| | 用户附和时继续说 ↑ | **96%** | 56% | 56% |
| | 对旁人说话时继续说 ↑ | **64%** | 0% | 0% |
| | 背景人声时继续说 ↑ | **84%** | 0% | 0% |
| | 交互处理质量 (语义判分) ↑ | **85.6%** | 51.0% | 53.1% |
| | 停止 / 回应延迟 ↓ | 1.61 / 2.59 s | 0.25 / 1.13 s | **0.20 / 1.06 s** |
| | 停顿时插话, 合成 / 真人对话 ↓ | 30% / 40% | **10% / 10%** | 10% / 60% |
| | 该接话时 2 s 内接上 ↑ | 80% | **100%** | 90% |
| 服务 | 单卡达标的最高并发 ↑ | 8 | 2 | **16** (接纳上限) |
| | 24 路 | 超时单元 20.5% | 未扫 (上限 16) | 112/128 被拒 |
| 听感 | 漏词率 ↓ | 6.0% | 6.1% (去掉截断的 0.8%) | **0.6%** |
| | UTMOS ↑ | 4.17 | **4.47** | 4.20 |
| | 音色相似度 ↑ | 76.2 | **83.6** | 67.3 |

注:
- 行为数据: v1.5 每类 25 对 (比例的 95% 区间约 ±20 个百分点); 停顿和接话两行是 v1.0, 用统一口径 (unified), 每子集 10 条 (约 ±30 个百分点).
- 服务数据: 每档 128 个会话.
- ↑ 越大越好, ↓ 越小越好, 粗体是每行最好的.

- **没有一种方案全面占优.**
  - 两个轮次制系统打断响应又快又准, 但把旁人说话、背景人声都当成在跟它说.
  - 原生全双工能分辨这两种情况, 但用户真打断时有一半不理, 平均 1.6 s 才停.
- **级联**: 容量最高、几乎不漏词, 但音色最不稳, 真人对话的停顿处 60% 会插话.
- **Qwen3-Omni**: 听感最好, 但单卡只扛 2 路.
- **只看任何一个维度, 都会得出相反的结论.** 三个维度在同一套协议下一起量, 是这套 benchmark 的价值.
- **评测顺带抓到几个系统问题** (见"发现的问题"): Qwen3-Omni 长回复被截断还报 completed, 级联会用中文回答英语用户. 达不到的指标后续优化, 改完用同样的命令重测对比.
- **自动化**: 整套流程是 bash 脚本: `servers.sh` 起三个服务, `bench.sh` 跑录制、打分、服务扫描, `collect.sh` 出表. 命令和步骤见`three-systems-20261019/REPRODUCE.md`; 指标优化后用同样的脚本重跑对比.
- **以哪个版本为准**: 评测工具以 sglang-omni main `a1939b97` 为准; 被测的三个系统都跑在私有 main `3dd888e0` 上. sglang-omni main 起 MiniCPM-o 那组只是容量排查, 不进主表.


## 设置

- 主机: hyper00, Radix 租约 (回执 `results/radix/20261019T163417Z-hyper00`), 4 张 H200 (宿主 GPU 1、2、5、6), 09:34 至 13:34 PT. 用户先要求尽量用 H100, 随后改回全部用 H200.
- 服务端: 私有 main `3dd888e0`, 一个容器三张卡:
  - MiniCPM-o: `--config examples/full_duplex/minicpmo.yaml --max_sessions 40` (私有 main 的全双工配置, 采样与官方 demo 一致: 温度 0.7、top_k 20、top_p 0.8), 模型用 runbook setup 下载的本地副本 (`503e754`), 端口 28097.
  - Qwen3-Omni: `examples/qwen3_omni/session_h200.yaml` (Session 图节点加 VAD, `max_sessions` 16), 端口 28965.
  - 级联: `qwen3-asr-qwen3-tts-customvoice` 改高位端口、对齐节点用 `method: asr`, 端口 28865.
- 客户端与打分: 公开 sglang-omni main `a1939b97` (已含 #2830 turn-based 录制与 #2925 听感指标, 两者 10-19 09:38、09:40 PT 由 Chenyang 合入), 另一个容器一张卡; FDB 打分用 runbook 的 `asr`、`judge` (`JUDGE=qwen`)、`aggregate`, `asr` 同时算听感指标. 客户端在 setup 阶段从本地合并分支换成了 main, 换之前没有录任何会话.
- 可复现: `bench.sh` 把每一步的完整命令和环境变量写进 `logs/commands.log`, 结束时记下两边代码版本和两个 Python 环境的 `pip freeze`; 这些与服务端启动命令一起整理进 `docs/runs/three-systems-20261019/REPRODUCE.md`.
- 样本: v1.5 每类前 25 对 (200 个会话), v1.0 每子集前 10 条 (50 个会话), 三个系统完全相同. 准确率录制每个系统单路 (一次一个会话), 三个系统并行, 各占一张卡.
- 轮次制两个系统: `server_vad`, 静音 800 ms.
- 服务指标: 每个系统扫并发 2/4/8/16/24/32 (Qwen3-Omni 到 16 为止, 它只开 16 路), 每档 v1.5 每类 16 对 (128 个会话); 单路的数据取自准确率录制. MiniCPM-o 看超时单元 ≤1%, 两个轮次制系统看回复实时率 p90 < 1.
- 脚本: `code/three_systems_20261019/` (`servers.sh`、`bench.sh`、`quiet.sh`、`public_ab.sh`、`collect.sh`、级联 profile).

## 过程

1. 09:34 PT 起租约, 09:50 PT 五个模型下载完. Qwen3-Omni 09:53、级联 09:58 PT 就绪开录.
2. MiniCPM-o 起了三次才成: 先照公开 main 的写法用 `--variant session`, 私有 main 已不认这个选项; 改用私有 main 文档里的 `--config examples/full_duplex/minicpmo.yaml`, 又缺 MiniCPM-o 的可选依赖 `onnx`; 装上 `.[minicpm-o]` 后 10:01 PT 就绪开录. 三次的服务端日志都在 `logs/srv-minicpmo-attempt*.log`, 实际执行的命令在 `logs/commands-servers.log`; `code/three_systems_20261019/servers.sh` 已改成最终生效的写法.
3. 三个系统并行录制、导出、扫描 (`bench.sh` 让三个系统同时跑, 各自单路录制), 打分按系统依次进行, 11:44 PT 结束. Qwen3-Omni 的 `asr` 在一段被打断后只剩 1 个采样点的回复上崩溃 (Parakeet `normalize_batch`). 修复是 sglang-omni#2963 (短于 25 ms 的回复不出 wav), 打上后 11:44 PT 重跑了它的 `asr` 与 `aggregate`.
4. 11:36 至 11:42 PT, 另外两个服务已经空闲 (bench 卡上还在跑级联的判分), 重扫 MiniCPM-o 的 C16、C20、C24 (`quiet.sh`), 用来检查主扫是否受同机负载影响.
5. MiniCPM-o 达标并发只有 8, 是 10-16 同型号卡的一半, 所以 11:55 PT 在 bench 容器的卡上起了公开 main 的 MiniCPM-o 做对照 (`public_ab.sh`).
6. `collect.sh` 汇总到 `docs/runs/three-systems-20261019/`, 复现步骤见其中的 `REPRODUCE.md`.

## 决策记录

| 问题 | 默认答案 | 理由 | 回滚 | 外审 |
| --- | --- | --- | --- | --- |
| 样本量 | v1.5 每类 25 对、v1.0 每子集 10 条 | 全量单路每个系统要约 9 小时; 这个子集约 70 分钟, 与 10-18 的听感对比同一批样本 | 换成全量只是改两个数, 脚本不变 | 未进行 (Chrome 未连接) |
| 准确率录制的并发 | 每个系统单路 | 并发会改变 FDB 的计时指标 | 改 `bench.sh` 的录制并发 | 同上 |
| 级联用哪个 profile | `customvoice` (纯 VAD 判轮) | 与 Junnan 10-17 的 FDB 结果和 10-18 的听感数据可比; Smart Turn (#45) 只接在 `base-clone` 上 | 换 profile 后重录级联一个系统 | 同上 |
| Qwen3-Omni 放哪 | H200 | 单张 H100 上 bf16 放不下 session 模式所需的 KV, FP8 会改变准确率 | 无 | 同上 |
| 判分模型 | 本地 Qwen3.8-27B (`JUDGE=qwen`) | 与 runbook 默认一致, 不需要外部 API | 用 `JUDGE=gpt` 重跑 `judge` | 同上 |
| 主机负载是否压低了 MiniCPM-o 的容量 | 另外两个服务空闲时重扫 C16、C20、C24 | 10-18 在 H100 上, 同机负载曾把 C10 推到 12.6% | 不需要 | 未进行 |
| MiniCPM-o 容量为什么只有 10-16 的一半 | 同机同客户端, 起公开 main 的 MiniCPM-o 对照 | 只差服务端代码与配置, 每档 2 到 4 分钟, 能在租约内定下来 | 不需要 | 未进行 |
| 私有 HF 写满后级联数据放哪 | 先在本机暂存; 用户 10-19 下午定为放公开库 | 私有 HF 存储已满, 充值要用户决定; Tilde、moss 连不上, aries 盘满, taurus 只许只读 | 已按用户决定上传公开库, 本机副本已删 | 未进行 |

## 结果

### FDB v1.5 (每类 25 对, Qwen 判分)

| 类别 | 应有行为 | MiniCPM-o | Qwen3-Omni | 级联 |
| --- | --- | ---: | ---: | ---: |
| user_interruption | 回应 (C_RESPOND) | 56% | 96% | 96% |
| user_backchannel | 继续 (C_RESUME) | 96% | 56% | 56% |
| talking_to_other | 继续 | 64% | 0% | 0% |
| background_speech | 继续 | 84% | 0% | 0% |
| 全部: 停止 / 回应延迟 (s, 越小越好) | | 1.61 / 2.59 | 0.25 / 1.13 | 0.20 / 1.06 |
| 语义判分: 交互处理 / 联合质量 (越大越好) | | 85.6% / 54.0% | 51.0% / 39.5% | 53.1% / 46.7% |

每类 25 个样本, 单个比例的 95% 区间约 ±20 个百分点. 按类别的完整表在 `three-systems-20261019/<系统>/RESULTS.md`.

### FDB v1.0 官方评测 (每子集 10 条, 区间约 ±30 个百分点)

| 子集 | 指标 | MiniCPM-o | Qwen3-Omni | 级联 |
| --- | --- | ---: | ---: | ---: |
| synthetic_pause_handling | 接管率 (越低越好) | 30% | 10% | 10% |
| candor_pause_handling | 接管率 (越低越好) | 30% | 10% | 60% |
| candor_turn_taking | 接管率 / 延迟 | 80% / 1.18 s | 100% / 1.04 s | 100% / 0.88 s |
| synthetic_user_interruption | 接管率 / 延迟 / 相关性 (0-5) | 90% / 1.48 s / 4.22 | 100% / 0.87 s / 5.00 | 100% / 0.73 s / 4.70 |
| icc_backchannel | 附和频率 / JSD | 0.000 / 1.000 | 0.000 / 1.000 (7 条) | 0.004 / 0.975 |

- 三个系统都基本不附和.
- Qwen3-Omni 的 icc_backchannel 只评到 7 条. 另外 3 条里用户一轮说得太长, 服务端收到的单个输入块 (1.09 至 1.34 MB) 超过 `max_chunk_bytes` 1 MiB, 会话被 fatal 终止.

### 服务指标 (单张 H200, 每档 128 个会话)

达标线: MiniCPM-o 要求超时单元不超过 1%; 两个轮次制系统要求回复实时率 p90 小于 1; 三个都要求没有失败会话. C1 一行取自准确率录制 (200 个会话). 完整表在 `three-systems-20261019/<系统>/SERVING.md`.

| 并发 | MiniCPM-o: 超时单元 / 首音 p90 | Qwen3-Omni: 失败会话 / RTF p90 / 首音 p90 | 级联: 失败会话 / RTF p90 / 首音 p90 |
| ---: | --- | --- | --- |
| 1 | 0.0% / 207 ms | 0 / 0.78 / 174 ms | 0 / 0.87 / 143 ms |
| 2 | 0.0% / 261 ms | 0 / 0.78 / 215 ms | 0 / 0.86 / 225 ms |
| 4 | 0.0% / 312 ms | **6** / 0.78 / 262 ms | 0 / 0.86 / 234 ms |
| 8 | 0.5% / 419 ms | 0 / 0.75 / 535 ms | 0 / 0.84 / 246 ms |
| 16 | **2.6%** / 865 ms | **69** / 0.70 / 4441 ms | 0 / 0.85 / 297 ms |
| 24 | **20.5%** / 1021 ms | 未扫 (上限 16) | **112** / 0.88 / 317 ms |
| 32 | **59.8%**, 7 个会话失败 | 未扫 | **122** / 0.86 / 339 ms |
| 达标的最高并发 | **8** | **2** | **16** |

安静重扫 (另外两个服务空闲时) 的 MiniCPM-o: C16 2.5%、C20 15.1%、C24 19.8%, 与主扫基本一样 (2.6%、无、20.5%). 本账号 cgroup 的 CPU 压力全程为 0, 所以主扫没有受同机负载影响.

失败原因 (逐会话的事件记录):

- **接纳上限** (级联 C24/C32, Qwen3-Omni C16):
  - 服务端先回 `session.created`, 收到 `session.update` 后发一个非致命 error, 内容是 `admission_rejected` "The request queue is full.", 而不是在握手时回 503.
  - 报告只把握手时的 503 算作拒绝接纳, 所以 503 一列是 0, 这些会话都记成了失败.
  - 被拒的会话立即关闭, 下一个样本马上补上又被拒, 所以级联 C24 只有最先进去的 16 个会话跑完 (128 − 16 = 112).
  - 级联 profile 没写 `max_sessions`, 第一批正好进去 16 个, 默认上限就是 16.
- **名额释放滞后** (Qwen3-Omni C16): 客户端同时开着的会话从不超过 16, 仍然被拒 65 次, 说明会话关闭后服务端没有及时释放名额.
- **显存** (Qwen3-Omni C4): 同一张卡上 thinker 占了 111 GB, 其他 stage 偶尔连 2 MiB 都分配不到. 5 个会话死于 cuDNN 注意力报错, 1 个死于 CUDA OOM, 都是 fatal. C8 没有复现.
- **压测端** (MiniCPM-o C32): 7 个会话是客户端发包迟到超过 80 ms, 不算服务端的问题.

### MiniCPM-o 容量排查 (不进主表)

三列都在同一台机器、同一个客户端、同一批样本上跑. 公开 main 用 runbook 的 H200 写法 (`--variant session --max_sessions 40`), 先跑 C8 预热. 表里是超时单元比例, 括号里是单元延迟 p99.

| 并发 | 私有 main `3dd888e0` (主扫 / 安静重扫) | 公开 main `a1939b97` | 参考: 10-16 公开 main `85d4219` |
| ---: | --- | --- | --- |
| 8 | 0.5% (810 ms) | 0.0% (580 ms) | 0.0% (501 ms) |
| 16 | **2.6% / 2.5%** (1125 / 1100 ms) | **0.6%** (944 ms) | 0.6% (923 ms) |
| 20 | 15.1% (安静重扫) | 未测 | 未测 |
| 24 | 20.5% / 19.8% | 6.1% (1309 ms) | 7.4% (1341 ms) |
| 达标的最高并发 | 8 | 16 | 16 |

- 公开 main 今天的数与 10-16 一致. 10-16 只计通过的会话, 口径略有不同, 但数值几乎一样.
- 私有 main 在同样条件下, C16 的超时比例是公开 main 的 4 倍, C24 是 3 倍多.
- 两边 `native_config.py` 里采样参数和各 stage 显存份额的默认值完全相同. 但公开 main 的 MiniCPM-o 多了 4 个 token2wav CUDA graph 相关文件 (`flow_cuda_graph.py`、`flow_graph_shapes.py`、`packed_dit_cuda_graph.py`、`fixed_packed.py`), 私有 main 一个都没有, 这是最可能的原因.
- 不过两份代码在 `sglang_omni/` 下共有 323 个文件不同, 要确认原因, 得把公开 main 同步进私有 main 后再扫一次.
- 完整表: `three-systems-20261019/minicpmo-public/SERVING.md`.

### 听感 (v1.5 全部类别)

| 指标 | MiniCPM-o | Qwen3-Omni | 级联 | 方向 |
| --- | ---: | ---: | ---: | --- |
| 回复数 (其中被取消) | 228 (0) | 300 (78) | 300 (80) | |
| 短于 3 s 的回复 | 11 | 43 | 42 | |
| 漏词率 (completed) | 6.0% | 6.1% (去掉截断的 0.8%) | 0.6% | 越小越好 |
| WER (completed) | 9.6% | 13.0% | 4.1% | 越小越好 |
| UTMOS 均值 / p10 | 4.17 / 3.79 | 4.47 / 4.42 | 4.20 / 3.70 | 越大越好 |
| 音色相似度均值 / p10 | 76.2 / 69.5 | 83.6 / 78.6 | 67.3 / 57.9 | 越大越好 |

- **Qwen3-Omni 的超长回复**:
  - 52 段回复超过 60 s. MiniCPM-o 和级联最长的回复分别只有 16 s 和 19 s.
  - 其中 8 段正好停在 327.7 s: 7 段在 v1.5 `user_backchannel` 的 clean 版本, 1 段在 v1.0 `candor_turn_taking`. 这些回复的文本最长有 1256 个词, 音频只念到一半左右, `response.done` 却仍报 completed.
  - 327.68 s 正好是 4096 个 12.5 Hz 的 codec token, 推测是 talker 的生成上限. 漏词率抓到的是这个截断.
- **与 10-18 对比** (`2026-10-18-cascade-vs-minicpmo-listening.md`, 同一批样本, MiniCPM-o 当时是公开 runbook 的服务端):
  - 级联: 漏词率 0.6% 对 0.4%, UTMOS 4.20 对 4.20, 音色相似度 67.3 对 67.5.
  - MiniCPM-o: 漏词率 6.0% 对 6.0%, UTMOS 4.17 对 4.24, 音色相似度 76.2 对 76.2.

## 发现的问题

系统问题已单独开 issue: Qwen3-Omni 的截断、长输入、显存问题见 #49, 级联的语种、音色、异常音频见 #50, MiniCPM-o 的容量差距见 #51. 第 4 条名额释放和第 5 条拒绝接纳是同一件事, 归 benchmark 客户端: 它对会话内的 `admission_rejected` 不做退避重试, 由 sglang-omni 侧修.

1. **Qwen3-Omni 回复被截断**: 音频停在 327.68 s, 文本照常生成完, completed 状态反映不出截断. 另外它对开放式提问常常一口气讲好几分钟.
2. **Qwen3-Omni 长输入被终止**: 用户一轮输入超过 `max_chunk_bytes` 1 MiB 时, 会话被 fatal 终止.
3. **Qwen3-Omni 4 路偶发显存不足**: thinker 显存份额太大, 其他 stage 余量不够.
4. **Qwen3-Omni 名额释放滞后**: 并发 16 时仍被接纳上限拒绝.
5. **拒绝接纳的信号与 benchmark 口径不一致**: 服务端用会话内的 `admission_rejected` 事件拒绝, 服务报告只认握手时的 503. 要么客户端把这个事件也计入 503 一列 (公开仓库改动), 要么服务端统一在握手时拒绝.
6. **级联的真实容量还不知道**: 要调高接纳上限再扫.
7. **私有 main 的 MiniCPM-o 落后于公开 main**: 同机对照下达标并发 8 对 16. 同步公开 main 的 MiniCPM-o (至少 token2wav CUDA graph).

## 级联换 Qwen3.8-27B (10-19 晚)

同事觉得 Qwen3-4B 太弱, 要求补一组 27B. 这一组只把级联的 LLM 换成 `Qwen/Qwen3.8-27B` (关闭 thinking), 其余条件全部不变: 私有 main `3dd888e0`, 客户端 `7ddb4364`, 样本 id 逐行相同, 打分相同.

**设置**
- **behavior:** hyper00 两张 H200, 借用 German data build 会话的租约, 经用户同意先停了它的容器. 每张卡一个副本, chat、ASR、TTS 三个服务在同一张卡上. 两个副本各录一半样本, 每个副本仍是单路. profile 见 `code/three_systems_20261019/cascade27b/`.
- **显存:** chat 0.55、ASR 0.16、TTS 0.16. 第一次按 0.62/0.08/0.12 启动时, ASR 报 KV 缓存放不下, 两个副本都没起来.
- **服务扫描:** hyper01 四张 H200, 四个副本. 并发 2、4、8、16 各占一个副本同时跑, 每档 128 个会话. 24 和 32 两档不测, 因为默认接纳上限是 16.

**结果** (v1.5 每类 25 个样本, 比例的 95% 区间约 ±20 个百分点)

| Metric | Cascade 4B | Cascade 27B |
| --- | ---: | ---: |
| Responds when the user interrupts | 96.0% | 72.0% |
| Keeps talking through a backchannel | 56.0% | 76.0% |
| Keeps talking when the user addresses someone else | 0.0% | 24.0% |
| Keeps talking through background speech | 0.0% | 12.0% |
| Overlap handled appropriately (LLM judge) | 53.1% | 54.2% |
| Relevance (LLM judge) | 100.0% | 95.5% |
| Grounding (LLM judge) | 71.9% | 87.2% |
| Joint quality (LLM judge) | 46.7% | 44.0% |
| Stop / response latency (s) | 0.20 / 1.06 | 0.17 / 1.32 |
| Speaks into a pause, synthetic / natural | 10% / 60% | 10% / 40% |
| Takes the turn within 2 s | 90% | 90% |
| Omission rate | 0.6% | 0.4% |
| UTMOS | 4.20 | 4.24 |
| Voice consistency | 67.3 | 67.9 |
服务: 2 到 16 路全部达标, 回复实时率 p90 在 0.80 到 0.84 之间. 首音 p50/p90 从 2 路的 466/680 ms 涨到 16 路的 822/1315 ms; 4B 同档的首音 p90 是 225 到 297 ms. 完整表在 `three-systems-20261019/cascade27b/SERVING.md`.

**读法**
- 27B 主要提升了回答内容: grounding 从 71.9% 升到 87.2%. 代价是回应延迟多约 0.26 s, 首音也明显变慢.
- 旁人说话和背景人声时, 27B 仍有 76% 和 88% 会去回应. 什么时候接话由 VAD 判轮决定, 不由 LLM 决定.
- 打断题的回应率从 96% 降到 72%, 差距在误差边缘. 同类的交互处理质量是 95.7%, 判分认为处理得当.

**过程中的问题**
1. 节点上的 `localhost/sglang-omni:dev` 是 data build 会话打的 `nvidia/cuda` 基础镜像, 里面没有 python. 改为按 digest 拉 `hongccc/sglang-omni@sha256:ebe4239e…`.
2. 单卡放三个服务时, ASR 的显存比例要提高到 0.16, 原因见上文设置.
3. hyper01 上 runbook 的 `setup` 要求 `CUDA_VISIBLE_DEVICES` 非空.

**产物**
- 小文件在 `docs/runs/three-systems-20261019/cascade27b/`: RESULTS.md、SERVING.md、serving.json、听感汇总、命令日志、版本、负载记录、与 4B 的对比表.
- 公开 HF `gavinlaw/sglang-omni-fdb-native-runs`:
  - `20261019-cascade27b-fdb/` (revision `64e3b9ca0121a9e345052ddfe9ec0dd65a0fb358`): 录音、打分和日志;
  - `20261019-cascade27b-serving/` (revision `270fa7dfd114fe00f5bd9022b6660f235dc8bcd7`): 服务扫描.
- 复现: `drive27.sh` 调起 `servers27.sh` 和 `bench27.sh` (behavior), `drive27s.sh` 调起 `servers27s.sh` 和 `sweep27.sh` (服务扫描). 都在 `code/three_systems_20261019/cascade27b/`, 逐条命令在上面的 commands 日志里.

**收尾**: 两边的容器都已删除. hyper01 租约 18:03 PT 释放, hyper00 租约 18:26 PT 释放 (data build 会话说它不再需要这个租约, 请我释放), 两次都用 `radix machines mine` 复核过.

## 产物

- **小文件**: `docs/runs/three-systems-20261019/`, 复现步骤在其中的 `REPRODUCE.md`. 包括:
  - 每个系统的 `RESULTS.md`、`SERVING.md`、`serving.json`、听感汇总和样本 id;
  - 安静重扫和对照组的服务表;
  - 命令日志、版本、负载记录、脚本和配置.
- **MiniCPM-o 与 Qwen3-Omni 的录音、扫描和打分中间产物**: 公开 HF 数据集 `gavinlaw/sglang-omni-fdb-native-runs`.
  - `20261019-three-systems-minicpmo-qwen3omni/`, revision `83626583d7df229c38ebe27d2ecd16360326c7d4`, 4 个 tar 加 `MANIFEST.json`, 大小核对一致.
  - 对照组在 `20261019-minicpmo-public-main-ab/`, revision `e0de15b40440850db1ba048f4a9b768f2b99a819`.
- **级联的录音、扫描和全部服务端日志**: 同一个公开数据集的 `20261019-three-systems-cascade/`, revision `808d0b92424158ca1c062b5aee7cf227449332e8`. 包括 `cascade-fdb.tar`、`cascade-serving.tar`、`logs.tar` 和 `MANIFEST.json`.
  - 先尝试的私有库写满了, 所以先在本机暂存. 用户 10-19 下午决定级联数据放公开库, 不用私有库.
  - 上传后按 HF 记录的大小和 LFS sha256 与 `MANIFEST.json` 逐个核对, 一致后删除了本机暂存的 `~/hf-pending/20261019-three-systems-cascade/`.
- **数据集说明**: README 已补上这三个目录的说明, revision `8bf89e0953cca8c33b5d7112375f950382d8cf3b`.

## 收尾

12:05 PT: 两个容器已删除, map 已清空, 节点上的 tmux 会话已关, 租约已释放 (`radix machines mine` 为空), 积分 99.
