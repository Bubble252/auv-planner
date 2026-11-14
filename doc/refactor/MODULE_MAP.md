# auv-planner Module Map

**状态**：`REF_GLOBAL_COMPLETE`<br>
**用途**：记录本 pilot 可修改模块的职责、边界、公共 API 和测试入口。

## 1. 模块清单

| 模块路径 | 主要职责 | 非职责 | 公共 API | 对应测试 | Owner | Waiver |
|---|---|---|---|---|---|---|
| `src/auv_planner/_json.py` | 稳定 JSON 文档文本和文件写出 | 不校验 schema、不创建实验目录语义 | 无（下划线内部模块） | `tests/test_json_io.py` | planner | 无 |
| `src/auv_planner/_csv.py` | M7 空结果合法 CSV 的字节稳定写出 | 不创建父目录、不推断 schema、不规范化 list 值 | 无（下划线内部模块） | `tests/test_csv_writers.py` | planner | 无 |
| `src/auv_planner/evaluation/runner.py` | 单场景评价、CSV 和 run log 写出 | 不定义 planner、scene 或 success 规则 | `EvaluationRecord`, `run_scenario`, `write_run_log` | `tests/test_runner.py` | evaluation | 无 |
| `src/auv_planner/evaluation/closed_loop.py` | 闭环评价编排和日志 | 不定义控制器或场景 | `ClosedLoopResult` 等 | 闭环评价测试 | evaluation | 无 |
| `src/auv_planner/scene_catalog.py` | M5 固定场景 catalog、manifest 和 digest | 不执行规划或评价 | `m5_scene_catalog`, `scene_catalog_manifest` | `tests/test_m5_scene_catalog.py` | scenes | 无 |
| `src/auv_planner/experiments/m4_closed_loop.py` | M4 旧路径兼容别名 | 不复制实验逻辑 | `M4Case`, `m4_cases`, `run_m4_suite` | `tests/test_g04_experiments_import_contract.py` | experiments | 无 |
| `src/auv_planner/experiments/m5_validation.py` | M5 旧路径兼容别名 | 不复制验证逻辑 | 原 `__all__` | `tests/test_g04_experiments_import_contract.py` | experiments | 无 |
| `src/auv_planner/experiments/m6_recovery.py` | M6 旧路径兼容别名 | 不复制恢复实验逻辑 | 原 `__all__` | `tests/test_g04_experiments_import_contract.py` | experiments | 无 |
| `src/auv_planner/experiments/m7_1/` | M7.1 旧 package 与子模块兼容入口 | 不复制审计、修复、I/O 或 runner 逻辑 | 原 `__all__` 和私有测试入口 | `tests/test_g04_experiments_import_contract.py` | experiments | 无 |
| `src/auv_planner/experiments/m7_2.py` | M7.2 旧路径兼容别名 | 不复制比较逻辑 | `M72Config`, `run_m7_2` | `tests/test_g04_experiments_import_contract.py` | experiments | 无 |
| `src/auv_planner/experiments/m7_budget.py` | M7 budget 旧路径兼容别名 | 不复制预算逻辑 | `M7Probe`, `run_m7_budget` | `tests/test_g04_experiments_import_contract.py` | experiments | 无 |
| `src/auv_planner/experiments/validation/closed_loop.py` | M4 闭环案例和 suite 编排 | 不实现控制器或评价器 | `M4Case`, `m4_cases`, `run_m4_suite` | `tests/test_control_remus100.py` | experiments | 无 |
| `src/auv_planner/experiments/validation/model_validation.py` | M5 模型验证、开闭环对比和报告 | 不修改 simulator、scene 或阈值 | 原 M5 公共名称 | `tests/test_m5_validation.py` | experiments | 存量文件/函数长度 |
| `src/auv_planner/experiments/validation/recovery.py` | M6 恢复场景、证书和 manifest | 不修改 recoverability checker | 原 M6 公共名称 | `tests/test_recovery.py` | experiments | 存量文件/函数长度 |
| `src/auv_planner/experiments/planner_bench/planner_comparison.py` | M7.2 planner/aggregate 对比和 artifact | 不修改 recoverability 判定 | `M72Config`, `run_m7_2` | `tests/test_m7_2.py` | experiments | 存量文件/复杂度 |
| `src/auv_planner/experiments/planner_bench/budget.py` | M7 预算、probe 和 hardware manifest | 不修改 scene 或 planner 契约 | 原 budget 公共名称 | `tests/test_recovery_query.py` | experiments | 存量文件长度 |
| `src/auv_planner/experiments/planner_bench/path_audit/` | M7.1 审计、修复、I/O 和 runner 实现 | 不修改 planner、case、阈值或 artifact schema | 原 `__all__` 和私有测试入口 | `tests/test_m7_1.py`、`tests/test_m7_1_golden.py` | experiments | 存量函数复杂度/长度 |
| `src/auv_planner/recovery/models.py` | 恢复证书和稳定摘要模型 | 不执行规划 | `RecoveryCertificate` 等 | `tests/test_recovery.py` | recovery | 无 |
| `src/auv_planner/recovery/query.py` | 恢复查询会话和状态机 | 不定义故障模型 | `RecoveryQuerySession` 等 | `tests/test_recovery_query.py` | recovery | 无 |
| `src/auv_planner/planners/recoverable.py` | 可恢复路径规划与证书生成 | 不实现全局评价协议 | `RecoverablePlanner` 等 | `tests/test_planning_baselines.py` | planners | 存量文件长度 |
| `scripts/run_m7_1.py` | M7.1 CLI 调度 | 不承载实验算法 | `main` | `tests/test_m7_1.py` | scripts | 无 |
| `scripts/run_m7_2.py` | M7.2 CLI 调度 | 不承载实验算法 | `main` | `tests/test_m7_2.py` | scripts | 无 |

## 2. 边界说明

| 层 | 允许依赖 | 禁止依赖 | 说明 |
|---|---|---|---|
| `evaluation` | `auv_core`、`auv_planner` 契约 | 训练仓库、外部 simulator 源码路径 | 评价只消费 planner 结果 |
| `experiments` | `auv_core`、planner、recovery、evaluation | `auv_local` / `auv_lowlevel` | 实验编排可以组合本仓库模块 |
| `planners` | `auv_core`、recovery 契约 | 训练环境和实验输出 | 规划算法不读 artifact |
| `recovery` | `auv_core`、数值库 | 具体 planner 或实验入口 | 证书与查询保持可复用 |

## 3. 变更规则

- 修改公共 API、manifest schema 或 seed/scene 语义时，先更新契约测试和 Goal。
- 内部 helper 使用下划线模块名；消费者不得依赖 `auv_planner._json`。
- 不在重构 commit 中批量格式化历史文件；候选文件单独检查。
- M5/M6/M7 的 manifest 字段和 digest 属于冻结行为，等价性优先于代码美观。
