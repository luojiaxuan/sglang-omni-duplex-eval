# #2994 A 组实机验证第三轮: 修复的 GPU 复验 (2026-10-28)

## 结论

- A18 (MiniCPM-o 回合在语音说完前结束): #3311 已合入 (fddaa669). 修复后 3 条被输入结束截断的回复都报 `incomplete` / `max_output_tokens` (main 上都是 `completed`), 3 条取消的回复报 `cancelled`; 完成会话里的 6 条回复有 2 条报 `incomplete`, 其中 1 条 ASR 确认末尾 4 个词没说出来 (模型自己结束回合时还有排队的文字), 另 1 条完整说完, 是误报. 在 #3155 的 10-23 FDB 录音 (234 条回复, 逐条用 Qwen3-ASR 转写对照文字) 上, "最后一个单元用满窗口" 标出 84 条末尾缺词回复中的 81 条, 同时把 49 条完整回复也标成 incomplete; 未标的 104 条只有 3 条缺词. main 的判据 84 条一条也标不出. 服务端无法区分 "用满窗口时恰好说完" 和 "说不完", PR 里写明了这个取舍.
- A5 (thinker 语音预算): #3312, 与 #3313 合在一起复验. 16 个要求长故事的提示 (中英各 8), 默认采样: 全部停在 483 token, 报 `incomplete` / `max_output_tokens`, 音频 1435 到 1937 帧 (115 到 155 s, 至多用到 talker 上限的 47%), 每 token 2.97 到 4.01 帧. 最慢的一条 ASR 末尾正是文字的最后一句, talker 全部说完.
- A2, Qwen3-Omni (#3313): 同一个 4 s 截断两次, 下一单元 thinker prefill 都是 172 token, main 上是 212, 少保留 40 个 token (main 53, 修复后 13). 追问 "And then?" 不再接着用户没听到的内容讲.
- A2, cascade 排队问题 (最新 main c7b09e42): 回复播放中提交 "And then.", 2027 ms 处取消并截断, heard `text_end=34`. 发给 LLM 的下一次请求里这条回复正是听到的部分 (`'I cannot tell a long story because…'`), 排队的问题随即得到回答, 追问也答了.
- #3255 中文: 以它的 base 785f1838 对照 head 663236e8, 两段 20 次打断的对话. base 40 条回复里 3 条以 "…" 结尾, 4 条空, 9 条过短, 中位 7 字; #3255 分别为 0, 0, 0, 中位 28 字, 全部是中文. 已 approve.
- A7: 最新 main 上并发压力 (session 上限 4, 空闲 20 s, 4 个客户端各 12 轮) 40 个功能 session 全部正常, 包括上轮没跑成的 "音频前取消" 8/8 (被切回复 `cancelled`, 下一问照常回答), 空闲 session 都在 20 s 被关闭, 无占位泄漏.

## 设置

- hyper01 2×H200 (GPU 5/6), 21:00Z 至 01:00Z 的租约, 23:25Z 前收尾释放. 先 Qwen3-Omni (#3312 与 #3313 合并的树) 与 MiniCPM-o (#3311) 各占一卡, 再停掉两者让级联用两卡.
- 源码树在节点上直接从公开仓库拉取 (`node/fetch-trees.sh`), 不经本机上传. 每阶段结束把节点日志拉回本机.

## 产物

- 公开数据集 `gavinlaw/sglang-omni-fdb-native-runs` 的 `a-group-live-20261028/`, revision f8fdcc28 (89 个文件, 含节点日志 `node-logs/*.tgz`, 其中级联 chat 请求日志即上面的历史证据).
- FDB 录音上的 A18 判据精度: 同目录 `a18-precision-fdb-20261023.json` 与 `a18_precision.py`.

## 判断记录

- #3255 的中文对照用它自己的 base 而非英文对照用的 e9c05846: 在 e9c05846 上 cherry-pick 有冲突, 用 PR 的 base/head 对照只差这一个提交, 别人可直接复现.
- A18 接受误报换召回: `incomplete` 的含义是 "文字可能长于音频", 误报只在保守一侧; 转写文字完整保留, 只有状态不同.
