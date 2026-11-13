# CSV Writer Audit

**状态**：`READ_ONLY_COMPLETE`<br>
**日期**：2026-11-13<br>
**范围**：`src/auv_planner/experiments/` 中 5 个 `_write_csv` 实现。

## 1. 结论

不能机械合并。五个 writer 对空输入、字段集合、父目录和列表值的处理不同；这些差异
属于实验 artifact 语义，不是单纯代码风格问题。GLOBAL-A4 只记录差异，不修改源码。

## 2. 差异表

| 模块 | 空 rows | 字段来源 | 父目录 | 列表值 | 当前语义 |
|---|---|---|---|---|---|
| `m5_validation.py` | `ValueError` | 所有 rows 的 key 并集 | 不创建 | 原样 | 允许不同行出现不同字段 |
| `m6_recovery.py` | `ValueError` | 第一行 key | 创建 | `list` 用 `|` 连接 | 兼容多值 delay/fault 字段 |
| `m7_1.py` | 写空文件 | 第一行 key | 不创建 | 原样 | 空结果也是有效 artifact |
| `m7_2.py` | 写空文件 | 第一行 key | 不创建 | 原样 | 空结果也是有效 artifact |
| `m7_budget.py` | `ValueError` | 第一行 key | 创建 | 原样 | 空结果视为协议错误 |

## 3. 为什么暂不合并

- 空输入在 M5/M6/M7 budget 是错误，在 M7.1/M7.2 是合法的空结果；
- M5 使用 key 并集，其他模块使用第一行 key；
- M6 对 list 做稳定连接，其他模块没有该归一化；
- 父目录策略不同，合并会把“创建目录”或“拒绝空结果”的行为错误地带到其他实验；
- 这些 artifact 可能被历史 Goal 的 summary/analysis 脚本读取，字节变化会污染复现。

## 4. 后续条件

未来若要统一，必须先为每个实验声明 artifact schema，并增加：

1. 空结果契约测试；
2. 字段顺序和缺失字段测试；
3. list 值编码测试；
4. 父目录和返回路径测试；
5. 历史 artifact 读取回归。

在这些测试完成前，CSV 写出保留原地实现。复制逻辑的清理留给 G04 的候选队列。
