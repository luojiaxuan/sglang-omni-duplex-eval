# 听感指标的 GPU 验证 (2026-10-18 晚, PT)

对应 #24 的前三项指标, 实现在 sglang-omni#2925 (`luojiaxuan/fdb-listening-metrics`). 设计笔记与决策记录见 `docs/reviews/2026-10-18-listening-metrics-design.md`.

## 设置

- 主机: hyper01, Radix 租约 `01M58QG2BZ23FJP80BC9175CZT`, 1 张 H200 (宿主 GPU 4), 17:03 至 17:33 PT 左右. 容器 `sglang-omni-jaxan-1`, 镜像 `hongccc/sglang-omni@sha256:ebe4239e…`.
- 代码: 录制与转写在 `0181d947`, 打分阶段在 `cb358abd` 重跑 (切分和转写的代码没变). runbook 用 `JUDGE=gpt` 跳过 27B 判分模型, 不跑 `judge`.
- 选样: `generate --v15-per-subset 4 --v10-per-subset 3 --num-shards 2`, 即 v1.5 32 个会话、v1.0 15 个会话. 全部通过, `asr` 106 s (含听感两个阶段).
- 脚本: `code/listening_20261018/` (`validate.sh` 主流程, `perturb_make.py` / `perturb_asr.py` 扰动, `duration_sweep.py` 截取扫描, `window_sweep.py` 窗口扫描).

## 结果

### 真实回复 (MiniCPM-o 4.5)

v1.5 `all`: 35 段回复, 1 段短于 3 s; 漏词率 4.2%, WER 7.3%, UTMOS 均值 4.27 (p10 3.89), 音色相似度均值 74.4 (p10 67.8). 4 个类别之间差别不大. 完整表 `docs/runs/listening-20261018/RESULTS.md`.

v1.0 的 `synthetic_pause_handling` (漏词 66.7%) 和 `icc_backchannel` (50.0%) 只有 2 段回复, 都短于 3 s. 逐段看是真实的文本与音频不一致: 例如协议文本 "That sounds", 音频只有 0.24 s, Parakeet 听到 "Right". 停顿处模型开口一个音节就转回听, 这正是 #24 说的"吞字", 漏词率抓到了.

### 受控扰动 (24 段 ≥2 s、≥5 词的 completed 回复, 每段 4 个版本)

| 版本 | 漏词率 | WER | UTMOS | 音色相似度 |
| --- | ---: | ---: | ---: | ---: |
| 原始 | 4.4% | 7.7% | 4.26 | 72.5 |
| 删掉中间 40% | **43.4%** | 48.9% | 4.04 | 72.8 |
| 每秒 10 个爆音 | 4.4% | 7.9% | **2.08** | 72.0 |
| 升 4 个半音 | 3.8% | 8.1% | 1.41 | **52.5** |

读法: 每个指标只对自己负责的缺陷敏感. 漏词率在爆音和变调下最多动 0.6 个点, 音色相似度在删音频和爆音下最多动 0.5. UTMOS 在删音频时降 0.22 (拼接处不连续), 在变调时也大跌, 因为相位声码器本身引入失真, 这一点不算串扰.

### 时长下限从哪来

1. **截取扫描** (`duration-sweep.json`, 6 s 以上的回复取中间一段, 与整段比):

| 截取长度 (s) | 0.25 | 0.5 | 1 | 1.5 | 2 | 3 | 4 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| UTMOS 偏差 | −2.07 | −1.10 | −0.38 | −0.15 | −0.06 | +0.07 | +0.05 |
| 音色相似度偏差 | −62.0 | −49.4 | −33.9 | −25.9 | −19.0 | −11.9 | −7.0 |

UTMOS 从 2 s 起无偏. 说话人向量在测到的所有长度上都依赖时长, 所以音色只能在等长窗口之间比.

2. **窗口扫描** (`window-sweep.json`, 窗口与下限取同一个值):

| 窗口 (s) | 1 | 1.5 | 2 | 3 | 4 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 能打分的回复 (共 50) | 46 | 45 | 45 | 44 | 38 |
| 原始与变调的区分度 d | 1.85 | 2.49 | 2.70 | 3.95 | 4.98 |

区分度一直随窗口上升, 覆盖到 3 s 只少 1 段, 到 4 s 少 7 段, 取 3 s. 这条曲线基于 MiniCPM-o 的回复长度分布; 级联的回复更短的话, 3 s 会排除更多回复, 届时用级联录音重扫一次.

## 产物

- 小文件: `docs/runs/listening-20261018/` (`RESULTS.md`、`listening-summary.json`、`perturb-summary.json`、两份扫描 json、`logs/driver.log`).
- 录音、逐段 wav 与扰动版本: HF 公开数据集 `gavinlaw/sglang-omni-fdb-native-runs` 的 `20261018-minicpmo-listening-validation/`, revision `b92dbf237f3dd2b64d57fce241878aa80362a4d5`, `run.tar` (runbook 的 `runs/listen`) 和 `perturb.tar` (扰动、扫描、日志、脚本) 加 `MANIFEST.json`, 大小核对一致.

## 收尾

17:33 PT 左右: 容器已删除, map 已清空, 租约已释放, `radix machines mine` 为空, 积分 99 (未续租).

## 待定

- 级联的录音 (录制目录, 含 `continuous.jsonl`、`playout.json`、`output-media.wav`) 还没拿到, 拿到后先用这套指标离线算一遍, 看能不能把"听着差"量出来.
- 级联的回复会被取消 (`cancelled`), 漏词率只比 completed 的; 若级联 completed 的回复很少, 需要另想办法比较被取消回复里已播出的部分.
