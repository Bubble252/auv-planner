# CSV Writer Audit

**状态**：`G04_CSV_EQUIVALENT_SUBSET_COMPLETE`<br>
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

## 5. G04-CSV 实施结果

`META-G04-CSV` 只迁移了 `m7_1.py` 与 `m7_2.py` 这一组完全同语义 writer：

- 空 rows：写空文件；
- header：第一条记录的 key 顺序；
- list 值：保留 Python 字符串表示，不做 M6 式 `|` 连接；
- 父目录：不创建；
- 换行：`newline=""` 与默认 CSV `\r\n`。

共享实现位于 `src/auv_planner/_csv.py`，两个原 `_write_csv` 保留为兼容 wrapper。
`tests/test_csv_writers.py` 对两个入口分别锁定空输入、特殊字符、列表值、换行和
父目录行为。

以下 writer 明确不迁移：

- `m5_validation.py`：拒绝空输入，并使用所有 row 的 key 并集；
- `m6_recovery.py`：拒绝空输入、创建父目录，并对 list 做 `|` 连接；
- `m7_budget.py`：拒绝空输入并创建父目录；
- `evaluation/runner.py`、`evaluation/closed_loop.py` 和 M4/M5/M6/M7 report writer：
  字段来源、返回路径或报告文本契约不同。

验证结果：

- 定向测试：`21 passed`（`test_csv_writers.py`、`test_m7_1.py`、`test_m7_2.py`）；
- 全量测试：`108 passed`；
- 改动文件 ruff / format：PASS；
- shape：`0 new violations, 119 suppressed`；
- dependency checker：PASS；
- mypy：`3 errors / 2 files`，与历史基线一致，无新增。
