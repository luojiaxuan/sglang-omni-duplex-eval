# #2994 A 组实机验证: 播放, 字幕, 截断, 生成上限 (2026-10-26)

## 结论

- A1 (级联 1.0x 播放): 通过. realtime 页面接 27B 级联, 冷启动, 两条 104 s / 160 s 长回复, 5 s 一批的突发下发, 中途打断, 全程倍速 1.0, 自动丢弃 0 ms. 正常结束的回复收到多少播多少; 被打断的回复只丢掉打断后的部分. 未实测: 切换后端 (需要同时有一个原生全双工后端), 由 `app.test.mjs` 覆盖.
- A3 (字幕跟随播放): 发现并修了一个 bug. 27B 和两个 Nemotron profile 没发布 aligner, 客户端收不到 `sglang.response.progress`, 字幕不跟音频. 修复是 sgl-project/sglang-omni#3239. 修后英文按词, 中文按字推进, 从不落后于已播位置; 只有每条回复开头第一个 progress 点到达前约 0.3 s 会整句显示为已听到 (页面对不发 progress 的部署的兜底).
- A2 (按播放位置截历史): main 上通过. 页面发 `conversation.item.truncate` (正确的 item_id 和 audio_end_ms), 服务端按 forced aligner 的词边界保留听到的部分, `sglang.response.heard` 与字幕一致 (例: 4613 ms 处保留 154 字符里的 70). #3207 的构建上没有回归.
- A5 (Qwen3-Omni 生成上限):
  - talker 上限: #3059 实机通过 (50 帧时 `incomplete` / `max_output_tokens`, 音频 3.98 s; 默认 4096 帧有 3/32 条撞上限, 也正确报 incomplete).
  - thinker 上限: 发现 bug, `max_new_tokens` 截断报成 completed. 修复是 sgl-project/sglang-omni#3240, 实机验证通过.
  - thinker 与语音的比例: 29 条正常结束的回复, 语音帧数 / thinker token 中位数 3.67 (英文 3.71, 中文 3.56), p10 2.95, p90 3.94, 最大 4.29. 默认 4096 帧只够约 1100 token (按最大比例约 955), 而 thinker 默认上限 2048, 所以长回复会出现文字比语音多.
- 附带发现 (不是管线 bug): 打断后的下一条回复, 27B 偶尔输出空回复或半句 (main 32 次打断中 5 次, #3207 11 次中 2 次, 另有 1 次可能是, 差异不显著). 调试日志显示 dialog 那一轮收到 0 个文本 delta, 是模型本身的输出, 与 #3187 记录的残留 (14%) 一致.

## 设置

- 代码: sgl-project/sglang-omni main 36341fc1. 对照构建: #3239 的 profile 改动, #3207 合入 main 后的 50b3a0ed, #3240 的 410fec56 (实测时是同一份源码的 7233d966).
- 级联: `qwen3-asr-qwen3.8-27b-vivian` (Qwen3-ASR-1.7B, Qwen3.8-27B, Qwen3-TTS-12Hz-1.7B-Base, Qwen3-ForcedAligner-0.6B), hyper00 2×H200, 服务端口改到 28xxx 以免撞车.
- Qwen3-Omni: `examples/qwen3_omni/session_h200.yaml`, hyper01 1×H200. 首次启动时 talker 编译 flashinfer MoE kernel 超过 600 s 无进度上限, 设 `SGLANG_OMNI_STARTUP_TIMEOUT=1800` 重启后正常.
- 页面: 本机 `playground/realtime/app.py` 与 `playground/cascade/app.py`, 经 SSH 隧道连到节点. 无头 Chrome (静音, 临时 profile) 通过 CDP 驱动: 麦克风换成按时播放的合成问题 (macOS 系统语音, 32 条中英), 记录播放 worklet 的状态与已播样本, 每 50 ms 采一次字幕.
- 租约: hyper00 2 卡与 hyper01 1 卡, 15:56 PT 起, 分别于 17:30 PT, 18:00 PT 左右释放, 没有续租.

## 关键数字

| 项 | 场景 | 结果 |
| --- | --- | --- |
| A1 | 冷启动 + 打断 (rt1b) | 首轮 7.68 s 全播; 打断的回复播 5.56 s, 丢 2.17 s; 后两轮 5.20 s, 4.88 s 全播 |
| A1 | 长回复 (rt2b) | 103.7 s, 160.0 s 全播, 倍速 1.0, 丢弃 0 |
| A1 | 5 s 突发 (rt3) | 队列最高 5.0 s, 95.9 s 全播, 丢弃 0, 4 次 underrun (两批之间播空) |
| A3 | main | 每条回复 0 个 progress 点 |
| A3 | #3239 | 165 s 英文 426 词 420 步; 100 s 中文 472 字 467 步; 突发下 108.8 s 回复 0 超前 0 落后 |
| A5 | thinker 16 token | main: completed / stop; #3240: incomplete / max_output_tokens |

## 产物

- 原始数据与脚本: 公开数据集 `gavinlaw/sglang-omni-fdb-native-runs` 的 `a-group-live-20261026/`, revision f79081a5 (README 在 630c02c9). trace 里删掉了麦克风输入音频, 保留模型输出.
- 本机工作目录 (不进 Git): `~/Downloads/S2S_omni/results/alive/`.

## 判断记录

- 打断后的空回复/半句归为模型行为, 不改管线. 依据: 调试构建上 dialog 那一轮 0 个文本 delta, TTS 收到的是 LLM 的 `turn.done`, bridge 的 turn 号也对得上. 若要处理, 方向是 #3187 的截断标记写法 (模型会模仿结尾的 "…").
- thinker 的预算怎么定 (按 talker 预算除以比例收紧 thinker, 还是放宽 talker) 留给 A5 负责人, 本次只提供比例数据和状态修复.
- 一次 4 路并发的测量里 en19 只生成 1552 帧却有 1594 token 且报 completed, 4 次重跑没复现, 记为未解释的单次异常.
