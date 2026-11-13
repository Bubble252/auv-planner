# auv-planner Refactor Inventory

**状态**：`REF_GLOBAL_INVENTORY_COMPLETE`<br>
**基线 commit**：`f606816`<br>
**日期**：2026-11-13<br>
**范围**：`src/auv_planner`、`scripts/`、`tests/`；不移动 artifact 或 checkpoint。

## 1. 规模

| 对象 | 数量 |
|---|---:|
| `src/` Python 模块 | 31 |
| `scripts/` Python 入口 | 12 |
| `tests/test_*.py` | 13 |
| 顶层包 | `control`, `dynamics`, `evaluation`, `experiments`, `planners`, `recovery`, `viz` |

入口职责清楚：`run_m*` 调用 experiments，`render_m*` 只读结果并生成可视化。主要
风险不在跨仓库依赖，而在 experiments/evaluation 内部重复的 CSV、JSON、report 和
manifest 写出。

## 2. 重复实现

| 重复模式 | 现状 | 风险 | 处置 |
|---|---|---|---|
| 稳定 JSON 文档写出 | `json.dumps(..., indent=2, sort_keys=True) + "\\n"` 出现在 scene catalog、M5/M6/M7 和 viz | 字段排序、缩进、末尾换行和父目录策略容易漂移 | 先抽一个只负责文本渲染的 helper，迁移有测试的 runner |
| 文件句柄 JSON 写出 | `evaluation/runner.py`、`evaluation/closed_loop.py`、`m7_2.py` | 写法不同，但当前都使用 indent=2、sort_keys=True 和末尾换行 | 与上一条统一到同一 helper，逐候选迁移 |
| `_write_csv` | M5、M6、M7.1、M7.2、M7 budget 各有一份 | 字段顺序、空值、换行和编码语义可能不同 | 先做只读差异表，不机械合并 |
| `_write_report` | M4、M5、M6 各有一份 | Markdown/report 内容与实验语义耦合 | 暂缓，必须有报告字节等价测试 |
| manifest 生成 | M5 scene、M6 recovery、M7 budget 等各有 manifest 函数 | 属于实验契约，不能改变 schema | 只统一写出边界，不改 payload |
| 入口参数解析 | 12 个 scripts 各自构造 parser | 参数语义不同 | 不做机械替换，只保留薄入口 |

## 3. 超大模块

| 文件 | 行数 | 说明 |
|---|---:|---|
| `src/auv_planner/experiments/m7_1.py` | 1483 | M7.1 实验、聚合和 artifact 写出 |
| `src/auv_planner/planners/recoverable.py` | 1144 | 可恢复路径规划与证书 |
| `src/auv_planner/experiments/m5_validation.py` | 1134 | M5 验证、报告和对比 |
| `src/auv_planner/experiments/m7_budget.py` | 851 | 预算实验和缓存审计 |
| `src/auv_planner/experiments/m7_2.py` | 750 | M7.2 实验、CSV 和 summary |
| `src/auv_planner/viz/m71_trajectory3d.py` | 745 | 3D 可视化 |

这些文件进入 `CODE_SHAPE_BASELINE.json`，本 pilot 不整文件重写。

## 4. 边界与冻结契约

- 只允许依赖已安装的 `auv-core`；不得导入 `auv_local`、`auv_rl`、`auv_lowlevel`
  或 `auv_isaaclab`，由 `tests/test_import_guard.py` 和跨仓库依赖检查器约束。
- M5 scene catalog、M6 recovery 和 M7 budget 的 manifest 是实验契约；重构只能保持
  字节或对象等价，不能改变 schema、seed、场景或门禁。
- PVS/MSS 外部资产通过 `PVS_SOURCE_DIR` / `MSS_SOURCE_DIR` 指定；不得写入固定
  服务器路径。
- 当前没有发现 `sys.path` 库注入；`test_import_guard.py` 在子进程中设置本仓库
  `src` 用于隔离检查，不是生产路径。

## 5. 候选队列

| 优先级 | 候选 | 边界 | 状态 / 前置证据 |
|---|---|---|---|
| P0 | GLOBAL-A1：稳定 JSON 文档 helper | 纯函数 + `evaluation/runner.py` 一个调用点 | IN_PROGRESS；字节等价测试和 runner 测试 |
| P1 | GLOBAL-A2：scene catalog 迁移到同一 helper | payload、digest 和父目录行为不变 | PENDING；catalog 测试 |
| P2 | GLOBAL-A3：M6/M7 manifest 迁移 | 只改写出边界，不改 manifest 字段 | PENDING；manifest 等价测试 |
| P3 | GLOBAL-A4：CSV 写出差异表 | 只读比较字段/空值/编码 | PENDING；不做合并 |
| P4 | 入口和超大模块拆分 | 一次一个职责 | PENDING；需单独 Goal 或明确候选 |

本 Goal 只执行 P0-P2 中有等价性证据的 manifest 收敛；CSV、report 和大模块拆分不
在本 pilot 中机械合并。

## 6. 只读盘点命令

```bash
cd /home/bubble/水下机器人/settled_全局规划器/.worktrees/ref-global-20261113
find src -type f -name '*.py' | wc -l
find scripts -maxdepth 1 -type f -name '*.py' | wc -l
rg -n 'json\.dumps|json\.dump|def _write_csv|def _write_report' src scripts
/home/bubble/水下机器人/.venv/bin/python \
  /home/bubble/水下机器人/总协调/scripts/check_code_shape.py --root . --check
```
