# 复现 2026-10-19 三系统 benchmark

本目录的数字都按下面的步骤跑出来. 每一步实际执行的完整命令和环境变量在 `commands.log` (录制、打分、扫描) 与 `commands-servers.log` (服务端重启和对照组服务端). 脚本原文就在本目录, 与 `code/three_systems_20261019/` 相同. 结果和解读见 `docs/runs/2026-10-19-three-systems-fdb.md`.

## 版本

| 项 | 版本 |
| --- | --- |
| 服务端 | 私有仓库 main `3dd888e02ac44fd64414241fc9ea55ab80a22adc` |
| 级联 profile | 在上面的基础上新增 `examples/streaming_cascade/profiles/qwen3-asr-qwen3-tts-customvoice-bench/launch.yaml` (本目录 `cascade-profile.yaml`): 由 `qwen3-asr-qwen3-tts-customvoice` 改成高位端口 (28100/28102/28105), 对齐节点用 `method: asr` |
| MiniCPM-o 配置 | 私有 main 的 `examples/full_duplex/minicpmo.yaml` (本目录 `minicpmo.yaml`), 命令行另给 `--max_sessions 40` |
| Qwen3-Omni 配置 | 私有 main 的 `examples/qwen3_omni/session_h200.yaml` (本目录 `session_h200.yaml`, `max_sessions` 16) |
| 客户端与打分 | sgl-project/sglang-omni main `a1939b97af92a5b8b944df74375ba766736e79ad`, 加 sglang-omni#2963 的补丁 (`7ddb4364`, 只改 `benchmarks/duplex/listening_replies.py`: 短于 25 ms 的回复不出 wav) |
| 对照组服务端 | 同一份公开 main `a1939b97` (`public_ab.sh`) |
| 模型 | 见 `model-and-data-revisions.txt`: MiniCPM-o 4.5 `503e754`, Qwen3-Omni-30B-A3B-Instruct `26291f7`, Qwen3-4B-Instruct-2507 `cdbee75`, Qwen3-ASR-1.7B `7278e1e`, Qwen3-TTS-12Hz-1.7B-CustomVoice `0c0e305`, 判分模型 Qwen3.8-27B `1d4bf0f` |
| 数据集 | FDB v1.5 `sha256:a1a3cd0d…`, v1.0 `sha256:103256ce…` (完整值在 `model-and-data-revisions.txt`), 由 runbook 的 `setup` 下载并校验 |
| 镜像 | `docker.io/hongccc/sglang-omni@sha256:ebe4239e29a764ee3a2806385c061c5fd438a26f01458e503d3822dcba5790df` (节点上重打为 `sglang-omni:dev`, image ID `2bac2617…`) |
| Python 环境 | 容器自带环境 `pip-freeze-client.txt`; runbook 的 scoring venv 没有 pip, 包列表用 `importlib.metadata` 导出到 `pip-freeze-scoring.txt` |

## 硬件

hyper00, Radix 租约, 4 张 H200 (宿主 GPU 1、2、5、6). 两个容器都用 `--network host`:

- 服务容器: 宿主 GPU 1、2、5, 每个系统一张卡, 跑三个服务.
- bench 容器: 宿主 GPU 6, 跑录制客户端、打分, 以及对照组服务端.

## 步骤

`<run>` 是节点上的运行目录, 容器内挂为 `/data/runs/20261019-three`.

1. 准备代码:
   - `<run>/priv`: 私有 main `3dd888e0`, 放进级联 bench profile.
   - `<run>/src`: 公开 main `a1939b97`, 打上 #2963 的补丁.
   - `<run>/pyshim`: 进程标题 shim, 只改进程名, 不影响结果.
2. bench 容器: 运行 `bash bench.sh <run> 3dd888e02ac44fd64414241fc9ea55ab80a22adc`.
   - 第一步是 runbook 的 `pip install -e .` 与 `python -m benchmarks.duplex.fdb setup`, 会把数据集、判分模型和 MiniCPM-o 本地副本下载到 `<run>/fdb`.
   - 之后脚本等服务就绪 (以 `/v1/models` 返回自己的模型名为准).
3. 服务容器: setup 下载完 MiniCPM-o 后, 运行 `bash servers.sh <run> <run>/fdb/models/MiniCPM-o-4_5`.
4. bench.sh 随后自动完成以下工作:
   - 选样: v1.5 每类前 25 对, v1.0 每子集前 10 条. 样本 id 存在各系统目录的 `v15-sample-ids.txt`、`v10-sample-ids.txt`.
   - 录制: 三个系统**并行**, 每个系统单路 (一次一个会话) 录制 v1.5 和 v1.0.
   - 导出, 然后做并发扫描: 每档 v1.5 每类 16 对, 即 128 个会话. 级联与 MiniCPM-o 扫 2/4/8/16/24/32, Qwen3-Omni 扫 2/4/8/16.
   - 打分: 按系统依次跑 `asr` (同时算听感指标)、`judge` (`JUDGE=qwen`)、`aggregate`.
5. 所有系统都停止工作后, 在 bench 容器运行 `bash quiet.sh`: MiniCPM-o 的 C16、C20、C24 重扫一遍.
6. bench 容器运行 `bash public_ab.sh`: 起公开 main 的 MiniCPM-o, 先跑 C8 预热, 再跑 C16、C24.
7. bench 容器运行 `bash collect.sh <run>`: 生成本目录的各系统 `SERVING.md`/`serving.json`, 并复制 `RESULTS.md`、听感汇总、样本 id 和配置.

## 与脚本不完全一致的地方

- **Qwen3-Omni 的 `asr` 跑了两次**. 第一次在一段被打断后只剩 1 个采样点的回复上崩了 (Parakeet `normalize_batch`). 打上 #2963 补丁后, 重跑了 `python -m benchmarks.duplex.fdb asr --run-name qwen3omni` 和 `aggregate --run-name qwen3omni`, 环境变量与 bench.sh 相同, 对应 `commands.log` 里的 `qwen3omni-asr-rerun` 一行. MiniCPM-o 与级联的 `asr` 都跑完了: 没打补丁的代码遇到这种回复必然崩, 说明这两个系统没有短于 25 ms 的回复, 补丁不会改变它们的结果.
- **MiniCPM-o 服务端起了三次才成**. 实际命令都在 `commands-servers.log`, 最终生效的写法就是 `servers.sh` 里的那条.

## 复现不了的部分

- **主机负载**: 同机有其他租户. `host-load.log` 每 5 秒记一次 1 分钟负载、系统 CPU 压力和四张卡的利用率. `user-cpu-pressure.log` 记本账号 cgroup 的 CPU 压力, 全程是 0.
- **采样**: 三个系统都按各自配置采样 (MiniCPM-o 的 temperature 是 0.7), 没有固定种子, 同一样本两次录制的回复会不同. 每个 v1.5 类别只有 25 个样本, 单次类别比例的 95% 区间大约是 ±20 个百分点; v1.0 每个子集只有 10 条, 区间约 ±30 个百分点.
