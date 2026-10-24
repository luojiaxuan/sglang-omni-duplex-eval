# Cascade causal replay (P0)

把 FDB 样本按 160ms 块、按墙钟节奏送进 判轮 → LLM → TTS。输出 `output.wav`(与输入时间轴对齐)和 `timing.json`,可以直接用官方 FDB 评分脚本打分。

| 配置 | 内容 | 状态 |
|---|---|---|
| `oracle` | 在标注的轮末时刻,用 ASR 转写(`prep_oracle.py`)直接起 LLM+TTS,只测后半段 | 已实现 |
| `turn` | SoulX-Duplug 判轮,不推测 | 已实现 |
| `spec-equal` | 推测执行,转写完全相等才复用 | 待做 |
| `spec-prefix` | 前缀验证,外加依赖安全的音频复用 | 待做 |

固定组件:
- LLM:Qwen2.5-7B-Instruct(SGLang),greedy 解码
- TTS:Qwen3-TTS-12Hz-1.7B-CustomVoice(sgl-omni),流式 PCM;英文用 Ryan,中文用 Vivian
- LLM 文本切段:首段在任一标点处切;之后只在句末标点处切
- 判轮:SoulX-Duplug@a0b9063;英文外挂 SenseVoice,中文外挂 Paraformer

数据:
- 英文:FDB v1 `candor_turn_taking`
- 中文:SoulX-Duplug-Eval@f6e50e8 中的 `Full-Duplex-Bench-zh` 轮转子集

## 运行(容器内,`<run>/src` 为本仓库)
```bash
bash src/benchmarks/cascade_replay/setup.sh <run> all
bash src/benchmarks/cascade_replay/serve.sh <run> en 4
<run>/turn-venv/bin/python src/benchmarks/cascade_replay/prep_oracle.py --data <subset> --lang en
python3 src/benchmarks/cascade_replay/replay.py --data <subset> --out <out> --lang en --mode turn \
  --turn-urls ws://127.0.0.1:810{0,1,2,3}/turn
```
打分:英文用官方 FDB `v1_v1.5/evaluation`(Parakeet ASR);中文用 SoulX `dialogue-system` 分支的 `eval/`(Paraformer ASR)。

## 记录
| 日期(PT) | 主机 / 卡 | 配置 | 结果 |
|---|---|---|---|
| 10-03 | hyper01 2×H200(LLM 卡 A,TTS 卡 B) | `oracle` en,119 条,8 路并发 | 从轮末到首个音频:P50 43ms、P90 78ms;其中 LLM 首 token 13ms,首段文本 20ms,TTS 首 PCM 22ms |
| 10-03 | 同上 | `oracle` zh,155 条,8 路并发 | P50 57ms、P90 79ms;LLM 首 token 14ms,首段文本 35ms,TTS 首 PCM 20ms |
| 10-03 | 同上,SoulX 与 LLM 同在卡 A | `turn` en,119 条,4 路并发 | 74%(88/119)在标注轮末之前开口;判轮服务每块处理 P50 74ms、P99 1.0s、最大 2.7s(单路时也如此),积压后轮末之后的延迟不可用 |

| 10-04 | hyper01 4×H200(LLM / TTS / SoulX-en / SoulX-zh 各占一张) | `oracle` en 119 条 / zh 155 条,8 路并发 | en:P50 41ms、P90 60ms;zh:P50 54ms、P90 78ms |
| 10-04 | 同上,1 路 | `turn` en(Candor 轮转) | 官方 FDB:TOR 0.874,延迟 0.282s(论文 0.933 / 0.511s)。76% 在轮末前开口;轮末之后首次判定 P50 1.15s,其中 26% 来自"等满 8 块"的兜底 |
| 10-04 | 同上 | `turn` zh(FDB-zh 轮转) | SoulX 评分:TOR 0.994,延迟 0.641s(论文 0.994 / 0.767s)。44% 在轮末前开口;轮末之后首次判定 P50 0.28s |
| 10-04 | 同上 | `turn` en(synthetic 停顿) | TOR 0.883(越低越好) |
| 10-04 | 同上 | `turn` zh(FDB-zh 停顿) | TOR 0.146(论文 0.038) |
| 10-04 | hyper01 4×H200 | 判轮离线扫描与 soulx-eos 端到端验证 | 见下文"判轮权衡曲线" |

判轮服务独占一张卡后,每块处理 P99 从 1.0s 降到 0.29–0.58s,秒级尖峰主要来自与 LLM 同卡。逐样本数据在本机 `results/p0/20261004-214407/`(不含 wav)。

P0 首轮结论(未经官方评分):
- 后半段(LLM+TTS)在 sglang-omni 上只需约 50ms,延迟几乎全部来自判轮。
- 推测执行在这套栈上最多能省约 50ms,P2 的优先级应让位于判轮。
- SoulX 在 Candor 英文上提前抢话很多。FDB 的轮转延迟把提前开口按 0 计,必须结合 pause 任务一起看。

已知问题:
- 判轮服务与 LLM 同卡时出现秒级处理尖峰,尚未确认是否源于同卡争抢。
- TTS 引擎不认 `--tts_engine.gpu_memory_fraction`,固定按 `mem_fraction_static 0.85` 分配,与 LLM 同卡会 OOM。
- dev 镜像 `hongccc/sglang-omni:dev`(09-08,sglang 0.5.19)跑不了 main(0.5.21),需用 Dockerfile 钉住的 base 镜像加 `setup.sh env`。

事故(10-03):
- 租约在逐样本结果拷回本地之前就到期了,`out/` 随节点个人目录丢失。上表数字来自当时的汇总输出。
- 起因是两条前台轮询命令(ssh 内的 curl 没设超时)挂起,被移到后台,各耗满 30 分钟。
- 对策:每跑完一组立即拷回;远程调用一律带超时;每一步之前先查租约剩余时间。

## 判轮权衡曲线(10-04 PT,hyper01 4×H200)
P0 已表明延迟几乎全在判轮,这一轮把判轮单独拿出来,在同一份数据上比较三类判轮器。

方法(`turn_log.py`、`eou_log.py`、`sweep.py`、`plot_sweep.py`;外审见 `docs/reviews/20261005_turn_sweep_review.md`):
- 逐块记录 SoulX 的状态 logit,接话分支一律改走等待;另记录 Silero 逐帧判定和静音段内每 160 ms 的 Smart Turn 分数。在日志上重放各策略,得到每个样本的第一次提交。在第一次提交之前,所有策略看到的模型轨迹相同,所以提交落在哪一块是精确的。
- 策略族:SoulX(margin、wait);soulx-eos(另外忽略说话中途直接输出的 complete,只在停顿处接话);sglang-omni semantic VAD(三档预设和单档网格);纯静音超时。
- 提交时刻计入 SoulX 的串行排队和接话时整段 ASR 的耗时(英 49 ms、中 93 ms,取自 10-04 回放),semantic VAD 按 160 ms 包时钟发出;音频起点再加固定后端延迟(41/54 ms)。
- 指标:1 s 内及时率(全部样本中,接话音频起点落在标注轮末之后 1 s 内的比例,提前和漏接都算失败)、提前率、停顿接管率(在标注停顿内提交)。

SoulX 不可复现:同一音频、同一随机种子跑两遍,逐块 logit 完全一致的只有 37/119 条,默认策略首次接话落在同一块的 90/119。首个差异出现在说话中途、logit 跳 1–6,应是外挂 ASR 或语音 token 的离散翻转;reset 填入的随机噪声也会改变近静音块的判定。单样本结论不稳,下表 SoulX 两行取 3 次抽样平均,聚合指标抽样间波动不超过 0.05,与 10-04 真实回放一致(英文提前率 0.72–0.78 对 0.76,中文 0.39–0.41 对 0.44)。

| 判轮 | 英 Candor 1 s 内及时 | 英提前 | Candor 停顿接管 | 中 FDB-zh 1 s 内及时 | 中提前 | 中停顿接管 |
|---|---|---|---|---|---|---|
| SoulX 默认(margin 0,wait 8) | 0.12 | 0.75 | 0.16 | 0.47 | 0.40 | 0.18 |
| soulx-eos(margin 0.5,wait 8) | 0.10 | 0.44 | 0.15 | 0.14 | 0.05 | 0.07 |
| soulx-eos(margin 1.5,wait 4) | 0.25 | 0.66 | 0.35 | 0.50 | 0.05 | 0.21 |
| semantic VAD medium(sglang-omni 默认) | 0.09 | 0.19 | 0.07 | 0.69 | 0.01 | 0.05 |
| semantic VAD(conf 0.5,640 ms,上限 800 ms) | 0.66 | 0.29 | 0.80 | 0.99 | 0.00 | 0.06 |
| 静音 800 ms | 0.67 | 0.28 | 0.76 | 0.95 | 0.00 | 0.03 |

结论:
- SoulX 的提前接话多数发生在用户还在说话时(模型直接输出 complete;中文 51/61,英文 73/93),margin 和 wait 管不到这条路径。去掉它后中文提前率从 0.40 降到 0.05,但要把 wait 调小才能保住及时率。
- 中文 FDB-zh 上,简单的静音超时和调过阈值的 semantic VAD 都明显好于 SoulX:合成集的轮内停顿短于 800 ms、轮末静音干净,对判轮偏容易。FDB 官方延迟把提前开口记为 0,掩盖了 SoulX 40% 的提前接话。
- 英文 Candor 上三类都差:停顿接管不超过 0.15 时,1 s 内及时率都不超过 0.16;800 ms 静音超时仍有 28% 提前。真人轮内长停顿才是判轮的难点,这也是需要真人中文集的原因(来源见 `docs/benchmark/zh_real_speech_sources.md`)。
- 曲线在同一测试集上选点,只作描述;每个子集 119–239 条,未划分开发集。

端到端验证(完整 LLM+TTS 链路,`turn_point.sh` 起 soulx-eos 服务,4 路并发,官方脚本评分;默认参数一行取 10-04 的回放):

| 点 | 提前率 离线 / 实测 | 1 s 内及时 离线 / 实测 | 停顿集任意接话 离线 / 实测 | 官方接话 TOR / 延迟 | 官方停顿 TOR |
|---|---|---|---|---|---|
| 英 SoulX 默认 | 0.75 / 0.77 | 0.12 / 0.12 | — | 0.874 / 0.282 s | —(10-04 未跑 Candor 停顿) |
| 英 soulx-eos(0.5,8) | 0.44 / 0.40 | 0.10 / 0.09 | 0.83 / 0.85 | 0.941 / 0.810 s | 0.690 |
| 中 SoulX 默认 | 0.40 / 0.44 | 0.47 / 0.49 | 0.35 / 0.34 | 0.994 / 0.641 s | 0.146 |
| 中 soulx-eos(1.5,4) | 0.05 / 0.02 | 0.50 / 0.45 | 0.59 / 0.58 | 1.000 / 1.541 s | 0.280 |

- 离线聚合值与端到端实测吻合(差距多在 0.04 以内),曲线可以代替逐点回放来选参数,端到端只需要抽查。
- 官方延迟把提前开口记为 0:英文提前率从 0.77 降到 0.40 后,官方延迟反而从 0.28 s 变成 0.81 s。比较判轮时应看 1 s 内及时率和提前率,不能只看官方延迟。
- 去掉说话中途的 complete 能压住提前接话,但在 FDB-zh 上要拿更高的停顿 TOR 和更长的延迟换,不是净收益。

产物:`docs/benchmark/turnsweep_20261004/`(sweep.csv、summary.json、三张曲线图);逐块日志在 HF 私有数据集 [gavinlaw/sglang-omni-cascade-turn-sweep-logs](https://huggingface.co/datasets/gavinlaw/sglang-omni-cascade-turn-sweep-logs)@5f59c74(逐块日志 6.3 MB、验证输出 1.4 MB,不含音频)。
