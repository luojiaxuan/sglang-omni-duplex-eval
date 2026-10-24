# 复现 judge 服务 Connection refused（2026-10-12）

## 问题

晨阳 10-11 的 preflight（sglang-omni#2696 评论 6106207170，当时分支约为 `19424c7`）：v1.5 Qwen judge 与语义 judge 都成功，v1.0 judge-free 三个子集也打完分，到 `synthetic_user_interruption` 第一个评审请求时报 `openai.APIConnectionError: Connection refused`。他没有贴 `judge-server.log`。

## 已排除（读代码）

- 地址不同：v1.0 评审与 v1.5 用同一个 `settings.judge_url`，同一个 `with judge_server(...)` 块内调用，块未提前退出。
- 代理环境不同：三类请求都由同一个 `run_command` 起子进程、同一份环境，OpenAI 客户端都默认 `trust_env`。
- `seed` 触发断言：sglang 0.5.21 只在开启确定性推理时才构造 `sampling_seed` 张量，judge 未开，`seed` 被丢弃。

## 线索

- tqdm 显示 `0/1 [00:06]`，两次重试的退避共约 1.25 s，环回地址上拒连是瞬时的，所以约 4.7 s 花在第一次请求上：第一次请求连上了活着的服务，之后服务消失。更像是这个请求把服务弄崩，而不是服务早已退出。
- 这是整个 judge 阶段唯一不带 `temperature` 的请求（官方评估器只传 `model`、`messages`、`seed`），走模型 generation_config 的采样参数；v1.5 两个 judge 都是 temperature 0。
- 反证：10-09 在 hyper01 上用手工起的 Qwen3.8-27B（sglang 0.5.21，`--context-length 32768`，无 `--reasoning-parser`）跑过 198 个 v1.0 打断评审请求，没有出错。runbook 起服务的参数不同（`sglang serve`、`--reasoning-parser qwen3`、`--mem-fraction-static 0.8`、不限上下文）。

## 复现设置

- 代码：sglang-omni main `7c3880cf048c8c76a20058edb2eeb9f229338f4f`（#2696 合入后），容器内可编辑安装。
- 主机：Radix hyper00，1 张 H200（宿主机编号 1），容器 `sglang-omni-jaxan-1`（保活命令 `sleep infinity`，脚本经 `podman exec -d` 启动，日志 `runs/20261012-192031/main.log`），租约 `01M4RRYED4PKZ92G181F56SWCP`，到期 10-12 15:20 PT；回执在本机 `results/radix/20261012T192031Z-hyper00`。
- 镜像：`hongccc/sglang-omni@sha256:ebe4239e…`（与 10-09、10-10 相同）。
- 命令：文档里的 preflight（`--v15-per-subset 1 --v10-per-subset 3`），judge 步加 `--log-level debug`，`FDB_WORK=/data/fdb`。
- 看护：preflight 约 15 分钟加 setup 下载；本机轮询主日志的阶段标记，停滞阈值 20 分钟。

## 环境上踩的坑（与 judge 问题无关）

1. 源码用 `git archive` 上传，`generate` 要 `git rev-parse HEAD` 记服务端版本，直接报错。在节点上 `git fetch` 同一提交并 `git reset`，工作区不变。
2. 镜像自带的 sglang 早于 main 的要求（缺 `sglang.srt.runtime_context.SpawnRanks`），`--no-deps` 可编辑安装不会升级它。改用 CI 的 `.github/scripts/prepare_omni_venv.sh` 建 venv。
3. 该脚本装 `sglang==0.5.21` 时把 venv 里的 NumPy 升到 2.5.4，而镜像里的 numba 0.65.1 要求 NumPy < 2.5（mistral-common 要求 < 2.4），MiniCPM-o 服务 import whisper 时失败。卸掉 venv 里的 NumPy，回落到镜像的 2.3.5 后正常。CI 不跑 MiniCPM-o，所以 CI 不会暴露这一点；照 CI 脚本给 runbook 建环境的人会撞上。
4. 更隐蔽的一层：runbook `setup` 第 1 步每次都用 `uv pip install --python <venv> einops onnx` 装 minicpm-o extra。CI 的 venv 通过 `.pth` 引入镜像的包，uv 看不到它们，于是给 onnx 重新装最新 NumPy（2.5.4），又把 numba 弄坏。复现脚本在 `setup` 后卸掉 venv 里的 NumPy 绕过。这是 runbook 与 CI venv 布局的配合问题，记作后续：要么让 extra 安装带上镜像已有包的约束，要么文档写明 venv 需完整安装依赖。

## 结果：两个版本都没有复现

| 代码 | 做法 | v1.0 打断评审 | judge 服务 |
|---|---|---|---|
| main `7c3880c` | 文档 preflight 全流程（v1.5 每类 1 对，v1.0 每子集 3 条），judge 步 debug 日志 | 3 个请求全部 200，平均评分 5.0，每个 1.5–2.8 s | 活到 runbook 发 SIGTERM（19:50:55Z），之后的 crash diagnostics 是正常停机的输出 |
| `19424c7`（晨阳当时的版本） | 复制上一行的录音与转写，删掉全部 judge 产物，只跑旧版 judge 步 | 3 个请求全部 200，平均评分 5.0 | 同上，19:58:04Z 收到 SIGTERM |

- 请求参数（台账 `user-interruption-*.jsonl`）：`max_tokens` 512、`enable_thinking` false、不带 temperature，即走模型默认采样。所以"非贪心请求把服务弄崩"在 H200 + sglang 0.5.21 上不成立。
- 旧版的调用顺序与晨阳的日志一致（v1.5 judge → 语义 judge → judge-free 的 v1.0 子集 → 打断子集，都在同一个 judge 服务里），也没出问题。旧版那次结尾的 v1.5 汇总告警（`tree changed since first phase`）来自我复制运行目录，与 judge 无关。
- 全流程的 RESULTS.md 两张表都正常出，可作 #2696 合入后的端到端冒烟记录。

## 判断与下一步

根因在晨阳的环境里，代码层面没有找到能触发它的路径。需要他提供三样东西：`/data/chenyang/fdb/runs/preflight/repeat-1/logs/judge-server.log` 的末尾约 50 行（服务退出前最后的日志）、serving venv 里的 sglang 版本、GPU 型号。用 main 重跑时 runbook 会在服务退出后直接报退出码和日志末尾。

## 产物与收尾

- 日志与台账：`docs/runs/judge-refused-repro-20261012/`（main 全流程的 judge、generate、asr、aggregate 日志，judge-server.log，v1.0 评审台账，RESULTS.md；`old-19424c7/` 下是旧版 judge 步的同类文件）。凭证扫描只命中字段名，没有 token。
- 收尾：10-12 13:00 PT 前后容器 `sglang-omni-jaxan-1` 已删除，map 记录已清除，租约 `01M4RRYED4PKZ92G181F56SWCP` 已释放，`radix machines mine` 为空，余额 100。
