# 级联与 MiniCPM-o 的听感对比 (2026-10-18 晚, PT)

#24 的核心问题: 级联在 FDB 上分数高但听着差, 新加的听感指标 (sglang-omni#2925) 能不能把"听着差"量出来. Junnan 只给了分数没有录音, 所以自己跑了级联, 并用同一批样本跑 MiniCPM-o 作对照.

## 结论

能量出来, 但差在音色一致性和低分尾巴上, 不在漏词上. 级联正常结束的回复几乎不漏词 (0.4%, MiniCPM-o 6.0%); 它的音色相似度低一截 (67.5 对 76.2), UTMOS 低分尾巴更重 (p10 3.63 对 3.90), 有 26% 的回复被打断取消, 还有 3 个英语会话里级联用中文回答. 用中文回答英语用户和 TTS 失控 (一句话后继续生成十几秒乱音) 是两个可以直接复现的具体问题.

## 设置

- 主机: hyper01, Radix 租约 `01M58YP5Q71B0DP6KQWM4CTEXA`, 2 张 H200 (宿主 GPU 6、7), 19:08 至 20:25 PT 左右. 两个容器: `sglang-omni-jaxan-1` (GPU 6) 跑级联服务, `sglang-omni-jaxan-2` (GPU 7) 跑 MiniCPM-o runbook、级联录制客户端和打分. 级联与 benchmark 依赖的 sglang-omni 版本不同, 所以分容器.
- 级联: 私有 main `95560828`, profile `qwen3-asr-qwen3-tts-customvoice` (Qwen3-ASR-1.7B、Qwen3-4B-Instruct-2507、Qwen3-TTS CustomVoice `Vivian`, 单卡), 改为高位端口, 对齐节点用 `method: asr` 代替强制对齐 worker (只影响打断后历史保留哪些字, 不影响合成音频). 文件 `code/listening_20261018/cascade-bench-profile/launch.yaml`.
- 录制: sglang-omni#2830 的 turn-based 客户端 (`--profile turn-based`, `server_vad` 静音 800 ms, 并发 2). benchmark 代码是公开 main `d72c5636` 合入 #2830 (`89ce4aa8`) 与 #2925 (`6f423d97`) 的本地分支 `36dd8ca4`.
- MiniCPM-o: runbook `generate --v15-per-subset 25 --v10-per-subset 10 --num-shards 2`, 再 `asr`、`aggregate`. 级联用同一份 `sample-ids.txt`.
- 样本: v1.5 每类 25 对 (200 个会话), v1.0 每子集 10 条 (50 个会话). 两边全部会话通过协议校验.

## 过程中的问题

1. **端口撞车**: 第一次把级联开在 18765, 同机别的租户的服务正占着这个端口, `/health` 立刻返回正常. 在对比脚本开录前发现并停掉, 改为 28765/281xx, 且以 `/v1/models` 返回本 profile 名作为就绪判据.
2. **中断的模型下载**: 停掉第一次尝试时 Qwen3-4B 正在下载, 残缺的快照让第二次起服务失败. 加了 `snapshot_download` 预下载步骤.
3. **协议校验不认识级联的扩展**: 级联授予 `client_commit: true`、`turn_control: ["server_vad", null]`, 并发送 `sglang.response.progress`. #2830 当时要求能力值完全相等, 200 个会话全判失败, 导出时全部不合格. 改为只检查录制器用到的部分 (`turn_control` 含 `server_vad`, `client_commit` 任意布尔值, 进度事件须指向已创建的回复), 推到 #2830 (`89ce4aa8`), 用 8 个真实级联会话离线重判全部通过后重录. 第一次的录制已作废, 未上传.

## 结果

### v1.5 全部类别

| 指标 | MiniCPM-o | 级联 | 方向 |
| --- | ---: | ---: | --- |
| 回复数 | 228 | 300 | |
| 被取消的回复 | 0 | 79 (26%) | |
| 短于 3 s 的回复 | 7 | 47 | |
| 漏词率 (completed) | 6.0% | 0.4% | 越小越好 |
| WER (completed) | 9.5% | 4.3% | 越小越好 |
| UTMOS 均值 / p10 | 4.24 / 3.90 | 4.20 / 3.63 | 越大越好 |
| 音色相似度均值 / p10 | 76.2 / 69.8 | 67.5 / 59.9 | 越大越好 |

按类别的并排表和 v1.0 表在 `docs/runs/listening-compare-20261019/compare.md`. 四个 v1.5 类别里级联的音色相似度都低 6.7 到 9.8 分; UTMOS 低分尾巴主要在 `background_speech` 和 `talking_to_other` (p10 3.49、3.36).

### 具体问题 (`reply-shape.json`)

- **换语言**: 级联 382 段有音频的回复里 8 段不是英语, MiniCPM-o 0 段. 逐段对照 MiniCPM-o 对同一样本的回答: `talking_to_other/8` 和 `background_speech/10` 的用户本来就让它翻成日语、法语, 这 4 段语言没错 (其中 2 段翻译的是旁人说的话或背景人声, 答错了对象, 这属于 FDB 已在测的行为). 另外 4 段在 3 个会话里 (`user_backchannel/12`、`candor_pause_handling/6`、`candor_pause_handling/7`), 用户说英语, 级联用中文回答, 例如 `嗯，时间旅行理论目前仍属科幻，尚未被证实。`, 这是真正的语言切换问题; 级联按识别到的语言回答 (私有仓库 #29), 应是识别把这几段英语判成了中文. 8 段非英语回复的音色相似度均值 45.7.
- **TTS 失控**: `background_speech/25` overlap 一段回复 18.6 s, 转写只有一句话 ("I don't eat, but I love pizza. Cheese and pepperoni, please."), 期间没有超过 2 s 的静音, UTMOS 1.67、音色相似度 31.5. 一句话之后继续生成了十几秒非静音音频.
- **只看英语回复**, 级联的音色相似度仍是 67.5, MiniCPM-o 76.1: 音色不稳不全是换语言造成的, 和 Junnan 说的"音调忽高忽低"一致.
- **静音**: 两边都没有超过 2 s 的回复内静音, 回复内最长静音的 p90 分别是 0.48 s 和 0.60 s.
- **漏词率低不代表没有吞字**: 级联被取消的 79 段回复不比漏词 (文本可能跑在音频前面), Junnan 听到的吞字可能出在这些被打断的句子上, 或出在网页播放器里 (私有仓库 #19).

## 产物

- 小文件: `docs/runs/listening-compare-20261019/` (`compare.md` 并排表与最差回复, `reply-shape.json`, 两边的 `summary.json`).
- 级联录音、逐段回复与日志: 私有 HF 数据集 `gavinlaw/sglang-omni-cascade-fdb-runs` 的 `20261019-cascade-vs-minicpmo-listening/`, revision `bf075e0bb3ee55b5703c06ba684840e0d08dfeb9` (级联未公开, 不放公开库).
- MiniCPM-o 的 runbook 结果: 公开数据集 `gavinlaw/sglang-omni-fdb-native-runs` 的 `20261019-minicpmo-listening-compare/`, revision `a215895603f9c04572fef397858cd6915d78ada2`.
- 脚本: `code/listening_20261018/` (`cascade_server.sh`、`compare.sh`、`cascade_record.sh`、`compare_report.py`、`reply_shape.py`).

## 收尾

20:25 PT 左右: 两个容器已删除, map 已清空, 租约已释放, 积分 99.

## 待定

- 换语言要不要成为一个指标 (回复语言与用户语言一致的比例): 现在是用字符集和停用词的粗判, 做成指标需要正经的语种识别, 还要排除用户要求翻译的样本 (如 `talking_to_other/8`).
- TTS 失控可以由"回复时长与文本长度之比"直接抓到, 比 UTMOS 更有针对性, 可作为下一项.
- 被打断回复的听感 (已播出部分是否在词中间截断) 还没有指标.
