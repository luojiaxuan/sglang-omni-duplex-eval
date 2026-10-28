# #2994 A 组实机验证第二轮: A2, A5, A7, A8, A18 (2026-10-27)

## 结论

- A8 (对齐归一化保留原文偏移): 通过. 5 句带数字, 连字符, 缩写的固定回复, 25 条回复, 455 个 progress 点, 10 次 heard 截断. 进度只前进, 播完的回复到达结尾, heard 不超过已播音频; 没有点落在数字或单词内部. 落在书写单位内部的点都在归一化本来就分开念的位置 (`12|%`, `7|:30`, `555|-0134`, `Dr|.`), 与 #3164 的设计一致. 收到第一个 progress 前约 0.3 s 页面把已流式到达的文字整段显示为已听到 (A3 已知的兜底), 这期间会出现数字中间的字幕.
- A7 (session 关闭与取消的竞争): #3273 已合入 (0d221fae). 并发压力 (session 上限 4, 空闲超时 20 s, 4 个客户端各 12 轮: 正常, 播放中取消, 回复中断连, 提问中断连, 空闲) main 与 #3273 结果相同, 无占位泄漏. 播放前取消的场景因压测客户端的 bug (问题后不留静音, VAD 收不到语音结束) 两边都没跑成, 待重跑.
- A2:
  - cascade 排队问题 (#3207): 回复播放中提交下一个问题, 4009 ms 处取消并截断, heard `text_end=70`, 排队的问题随即得到回答. 后续追问那步因脚本多等一个 `response.done` 未跑成, chat 请求日志随租约到期丢失, 待重跑.
  - #3255 (被打断的回复改写为 user 消息里的注记): 英文两段 20 次打断的对话, main 40 条回复里 4 条以 "…" 结尾, 4 条空, 9 条不足中位长度一半 (中位 33.5 字符); #3255 分别为 0, 0, 1 (中位 106.5). 中文 #3255 一段 20/20 全是完整句子, 全部仍是中文. 中文 main 基线两段都在驱动的单步 300 s 上限处超时, 待重跑.
  - Qwen3-Omni, 未听到的回复: 第一个转写 delta 时取消, 无音频送出, 下一单元 prefill 113 → 137 token, 回复被丢弃, 追问得到从头讲起的回答 (#3145 在 GPU 上成立). 若取消后服务端仍送出 0.78 s 音频而客户端不发 truncate, 服务端按已送出音频保留.
  - Qwen3-Omni, 部分播放后截断: 新发现的 bug. 4033 ms 处截断, 历史保留 53 token, 而前 4.03 s 音频的 ASR 只有 14 token ("Once upon a time, in a mountain range far beyond the reach of human"). `thinker_session.heard_tokens` 按每 80 ms 一个文本 token 换算, talker 实际约 3.7 帧一个 token. 下一条回复从用户没听到的内容接着讲.
- A18 (MiniCPM-o 回合在语音说完前结束): 新发现的 bug. 3 条被输入结束截断的回复都报 `completed` / `stop`, ASR 显示末尾 1 到 3 个词没说出来. 服务端逐单元打印: 回合最后一个单元用满 25 个码本槽时, EOS 落在窗口的额外槽, finish 为 `stop` (25 token), 而 #3155 只认 `length`. 修复是 sgl-project/sglang-omni#3311, GPU 复验待下个租约. 正常结束与取消的回复状态都正确.
- A5 (thinker 语音预算): 193 条自然结束的回复 (talker 上限调到 16384), token 6 到 1830, 每 token 帧数中位 3.69, 最大 6.90 (报国土面积的列表, 数字念得慢). 最慢包络 frames ≤ 600 + 4.40·tokens. 余量与 4096 帧对应的 thinker 预算: 1.0 → 793, 1.25 → 607, 1.5 → 483, 2.0 → 328; 留出一半检验时超出 m 倍包络的回复 (共 97): 1.87, 0.67, 0.03, 0. 余量的取舍与边界条件在外审后定 (`docs/reviews/`).
- 附带发现: Qwen3-Omni 16 路并发时, 长回复 (音频 43 到 70 s) 有 9 条以 `output of graph node 'qwen_omni' exceeds max_output_bytes 33554432; the client is not reading` 结束, 而客户端在持续读取. 这些回复不计入 A5 拟合.

## 设置

- 代码: main e9c05846; 对照 #3273 (27484890), #3255 (97d8ee4a, 基于同一 main).
- hyper01 4×H200 (GPU 1/2/4/5), 16:56 至 20:56 PT 的租约; 级联 `qwen3-asr-qwen3.8-27b-vivian` 占 2 卡, Qwen3-Omni (`session_h200.yaml`) 1 卡, MiniCPM-o 4.5 (`--variant session`) 1 卡. 镜像按 digest 拉 hongccc/sglang-omni.
- 页面类检查用无头 Chrome 驱动本机 `playground/cascade`; 其余用脚本直连 realtime. 音频转写用级联自带的 Qwen3-ASR-1.7B.
- 本机睡眠, 租约到期后被平台释放, 节点侧日志 (级联 chat 请求日志, MiniCPM-o 调试输出) 随之清空; 本机结果完整.

## 产物

- 原始数据: 本机 `~/Downloads/S2S_omni/results/alive/out/g1027/` (不进 Git), 待上传公开数据集 `gavinlaw/sglang-omni-fdb-native-runs`.

## 判断记录

- A8 判为通过: 书写单位内部的点都在归一化分开念的边界上, 写出来的前缀如实对应用户听到的内容 ("before 7" 对应 "before seven").
- A18 的判据从 finish reason 改为最后一单元是否用满窗口: #3155 自己的 FDB 证据用的就是这个特征 (最后一块 30720 采样以上), GPU 上的 finish reason 与单测假设不同.
