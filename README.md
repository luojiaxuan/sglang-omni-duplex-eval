# sglang-omni 全双工评测记录

SGLang-Omni 上三种语音交互方案的评测记录: 原生全双工 (MiniCPM-o 4.5)、轮次制 omni (Qwen3-Omni 加 VAD) 和级联 (ASR → LLM → TTS). 主评测是官方 Full-Duplex-Bench v1.5 与 v1.0, 另有服务并发扫描和听感指标.

评测客户端、打分和 runbook 在上游仓库 [sgl-project/sglang-omni](https://github.com/sgl-project/sglang-omni) 的 `benchmarks/duplex/` 与 `docs/developer_reference/full_duplex_bench.md`. 本仓库只放每次运行的记录、决策、外审和编排脚本.

## 当前结论

- 三种方案在同一套客户端和打分下的主表见 [2026-10-19-three-systems-fdb.md](docs/runs/2026-10-19-three-systems-fdb.md): 没有一种方案全面占优. 两个轮次制系统打断响应快, 但把旁人说话也当成在对它说; 原生全双工分得清, 但真打断时一半不理.
- 级联的音色跳变来自每次 TTS 请求独立采样. 每句都从同一段录音的说话人向量克隆后, 音色一致性 67.3 → 76.8, UTMOS 4.20 → 4.52, 响应延迟不变. 见 [2026-10-20-cascade-voice-anchor.md](docs/runs/2026-10-20-cascade-voice-anchor.md) 和 sgl-project/sglang-omni#3012.

## 目录

| 路径 | 内容 |
| --- | --- |
| `docs/runs/<日期>-<主题>.md` | 每次运行的记录: 设置、过程、结果、决策四件套 |
| `docs/runs/<主题>-<日期>/` | 该次运行的结果表、汇总 JSON、复现命令与脚本副本 |
| `docs/reviews/` | 外审 (ChatGPT) 的提问与全文回复 |
| `docs/design/` | 设计文档: 级联系统实现计划、半双工端点评测差距 |
| `docs/benchmark/` | 早期的判轮扫描与中文真人语音来源 |
| `code/<主题>_<日期>/` | 各次运行的编排脚本 (Radix 节点上的容器发射、录制、打分、上传) |
| `benchmarks/cascade_replay/` | 级联判轮的离线回放与扫描工具 |

## 运行记录

| 日期 (PT) | 记录 | 内容 |
| --- | --- | --- |
| 10-09 | [fdb-native-eval](docs/runs/2026-10-09-fdb-native-eval.md) | 原生全双工模型的 FDB 完整评测 |
| 10-09 | [fdb15-minicpmo-120](docs/runs/2026-10-09-fdb15-minicpmo-120.md) | FDB v1.5 一键流程, MiniCPM-o 每类 30 对 |
| 10-10 | [turn-sweep-qwen3omni](docs/runs/2026-10-10-turn-sweep-qwen3omni.md) | 轮次制端点的判轮参数扫描 |
| 10-12 | [judge-refused-repro](docs/runs/2026-10-12-judge-refused-repro.md) | 复现 judge 服务 Connection refused |
| 10-14 | [fdb-main-native](docs/runs/2026-10-14-fdb-main-native.md) | 主表录制: MiniCPM-o 原生全双工 |
| 10-15 | [ci-smoke](docs/runs/2026-10-16-ci-smoke.md) | MiniCPM-o FDB 的 Omni CI 阶段 |
| 10-15 | [minicpmo-capacity](docs/runs/2026-10-16-minicpmo-capacity.md) | MiniCPM-o 单卡承载上限 |
| 10-17 | [turn-based-client](docs/runs/2026-10-17-turn-based-client.md) | 统一客户端公开 |
| 10-18 | [minicpmo-h100-capacity](docs/runs/2026-10-18-minicpmo-h100-capacity.md) | MiniCPM-o 单张 H100 承载上限 |
| 10-18 | [listening-metrics-validation](docs/runs/2026-10-18-listening-metrics-validation.md) | 听感指标的 GPU 验证 |
| 10-18 | [cascade-vs-minicpmo-listening](docs/runs/2026-10-18-cascade-vs-minicpmo-listening.md) | 级联与 MiniCPM-o 的听感对比 |
| 10-19 | [three-systems-fdb](docs/runs/2026-10-19-three-systems-fdb.md) | 三种方案的主表、服务指标与 27B 级联 |
| 10-20 | [cascade-voice-anchor](docs/runs/2026-10-20-cascade-voice-anchor.md) | 级联音色: 每句克隆同一段锚点 |

## 数据

录音、逐段回复音频、分数和日志都在公开数据集 [gavinlaw/sglang-omni-fdb-native-runs](https://huggingface.co/datasets/gavinlaw/sglang-omni-fdb-native-runs). 每篇记录写明了对应目录和不可变 revision.

## 来源

- 2026-10-24 从私有仓库 `lijrjyan/sglang-omni-cascade-private` 的 `luojiaxuan/fdb-native-eval` 分支 (提交 `9e13d1ec`) 迁来, 只导入评测相关文件, 不含私有仓库的代码与提交历史.
- 记录里指向该私有仓库的链接 (issue #2、#24、#49 到 #51 等) 对外不可见.
- 团队飞书 RFC 的链接改成了文字引用.
