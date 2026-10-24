# 统一 client 公开 (2026-10-17, PT)

## 决定

- session 协议的 `turn_based` 服务端实现 (Session 图, `SessionBridge`, 级联) 暂不进开源 main, 留在私有仓库.
- benchmark client 公开: luojiaxuan 确认公开 `turn_based` 模式的接口细节 (事件, 字段, 回复的结束状态) 没有问题. client 只按 realtime 协议收发和检查, 不依赖服务端代码, 服务端在哪个仓库都不影响它.
- 因此 sglang-omni#2830 重新打开并转为正式 PR: 一套录制端同时支持 native 全双工和 `turn_based`, v1.5 与 v1.0 都能导出, 基于 main `c206fa3`, 提交 `fc2c4106`, 477 个单元测试通过. 已请 review.
- 经过: 同日上午曾把这部分误判为"超出开源范围", 关了 #2830 并把 client 放进私有分支 `luojiaxuan/fdb-turn-based-client`; luojiaxuan 指出接口和实现是两回事后改回公开, 私有分支已删除 (内容与 #2830 的 `fc2c4106` 相同, 只差提交信息).
- 服务端删旧协议 (Qwen3-Omni 改走 `turn_based`) 归 Junnan 的 Session 改造, 只在私有仓库做; 公开 main 上的 Qwen3-Omni 仍是旧协议, 所以公开 benchmark 的旧协议支持保留.

## 待办

- 和 Junnan 对齐: 他 10-16 说 FDB 测级联"只需做一点调整, 避免额外的返回内容被协议检查判成失败", 并在跑全量. 把他的调整并进 #2830, 用同一个 client 测级联和 Qwen3-Omni 节点.
