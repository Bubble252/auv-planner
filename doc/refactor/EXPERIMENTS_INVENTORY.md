# auv-planner Experiments Inventory

**状态**：`G04_EXPERIMENTS_E0_COMPLETE`<br>
**仓库**：`settled_全局规划器`<br>
**基线**：`main@e55cf5f`<br>
**日期**：2026-11-14

## 1. 范围与基线

`META-G04-EXPERIMENTS` 只归组 `src/auv_planner/experiments/` 中的实验编排模块。
不修改 planner、recoverability、评价阈值、scene、seed、matrix、artifact schema 或
报告字段。

- 拆分前全量测试：`109 passed`；
- shape：`0 new / 117 suppressed`；
- dependency：`ok`；
- 公共稳定入口：`src/auv_planner/experiments/__init__.py`。

## 2. 模块清单

| 旧路径 | 行数 | 主要职责 | 非职责 | 目标路径 | 风险 |
|---|---:|---|---|---|---|
| `m4_closed_loop.py` | 279 | M4 闭环案例和 suite 编排 | 不实现控制器或评价器 | `validation/closed_loop.py` | 低 |
| `m5_validation.py` | 1134 | M5 模型验证、开闭环对比和报告 | 不修改 simulator 或 scene 契约 | `validation/model_validation.py` | 中 |
| `m6_recovery.py` | 653 | M6 恢复场景、证书和 manifest | 不修改 recoverability checker | `validation/recovery.py` | 中 |
| `m7_2.py` | 744 | M7.2 planner/aggregate 对比和 artifact | 不修改 recoverability 判定 | `planner_bench/planner_comparison.py` | 中 |
| `m7_budget.py` | 848 | M7 预算、probe 和 hardware manifest | 不修改 scene 或 planner 契约 | `planner_bench/budget.py` | 中 |
| `m7_1/` package | 1581 | 路径审计、修复、I/O 和 benchmark 编排 | 不修改 planner、case、阈值或 artifact schema | `planner_bench/path_audit/` | 高，E3 |

## 3. import 边

- `validation/model_validation.py` -> `validation/closed_loop.py`；
- `validation/recovery.py` -> `auv_planner.recovery`、`auv_planner._json`；
- `planner_bench/planner_comparison.py` -> `planner_bench/path_audit`、
  `planner_bench/budget`、planner 和 recovery；
- `planner_bench/budget.py` -> `validation/recovery.py`、`auv_planner.recovery`；
- `planner_bench/path_audit/io.py` -> `planner_bench/budget.py`；
- `planner_bench/path_audit/runner.py` -> `planner_bench/budget.py`。

迁移后相对 import 深度增加一级；所有改动只做 `..` 到 `...` 的机械调整，不改变
导入对象或调用顺序。

## 4. 调用方与公共名称

| 旧模块 | 主要调用方 | 必须保留的名称 |
|---|---|---|
| `m4_closed_loop` | `experiments.__init__`、M4 script、控制测试 | `M4Case`、`m4_cases`、`run_m4_suite` |
| `m5_validation` | M5 script、M5 测试 | `run_m5_validation` 及其测试访问的案例/比较 helper |
| `m6_recovery` | M6 script、recovery 测试、M7.2/M7 budget | `dead_end_scene`、`m6_config_manifest`、`run_m6_recovery` 等 |
| `m7_2` | M7.2 script、M7.2/CSV 测试 | `M72Config`、`run_m7_2`、`_write_csv` 等 |
| `m7_budget` | budget scripts、visual review、recovery query 测试 | `M7Probe`、probe/manifest/run helper |
| `m7_1` | experiments re-export、m7_2、M7.1 scripts/tests | 原 package `__all__`、`_plan_request`、`_write_csv` |

## 5. 兼容层策略

旧 `m*.py` 保留为兼容别名模块：导入新实现后，把旧模块名在 `sys.modules` 中指向
新模块对象。这样旧/新路径得到同一对象，模块级 monkeypatch 也命中同一命名空间。

`m7_1/` 旧 package 在 E3 中保留根 `__init__.py` 和既有子模块路径；子模块兼容入口
只转发到新实现，不复制业务逻辑。E3 开始前必须重新运行 `m1`/全量测试、固定 fixture
字节对比和 import smoke。

## 6. 分批 Gate

| 批次 | 范围 | Gate |
|---|---|---|
| E0 | inventory、import graph、public API、fixture 清单 | 文档与 mapping 完整 |
| E1 | M4/M5/M6 -> `validation/` | 旧/新 import、全量测试、fixture 输出不变 |
| E2 | M7.2/M7 budget -> `planner_bench/` | E1 通过；CSV/report 字节不变 |
| E3 | M7.1 package -> `planner_bench/path_audit/` | E1/E2 全部通过；旧子模块与 golden artifact 不变 |

任何批次出现 import 身份不一致、输出漂移、全量测试退化、shape 新增或 dependency
失败，立即停止该批并保留回滚点。

## 7. E0 证据

- 基线全量测试：`109 passed`；
- `experiments.__init__` 当前导出 31 个公共名称；
- `m7_1` 已拆为 `types/audit/repair/io/runner` 五个实现模块；
- 没有发现测试通过 `monkeypatch` 修改 `m*.py` 模块级名称；
- 旧 module import 是当前主要契约，因此使用模块对象别名而不是复制实现。
