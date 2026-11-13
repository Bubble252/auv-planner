# Planner Boundary Audit

**状态**：`READ_ONLY_COMPLETE`<br>
**日期**：2026-11-13<br>
**范围**：`interfaces.py`、`dynamics/mss_remus100.py`、`tests/test_import_guard.py`。

## 1. 接口边界

- `GlobalPlanner` 只包含 `plan(request) -> PlanResult`；
- `LocalPlanner` 只包含一个 `act(...)`；
- 两者都是小而专一的 `Protocol`，没有万能接口或空壳抽象；
- `Guidance`、`SafetyFilter`、`SimulatorBackend`、`TrackingController` 来自
  `auv_core.interfaces` 的稳定契约，本仓库不复制实现。

结论：接口粒度符合 `CODE_STYLE.md` 第 8.1 节，本 pilot 不修改 `interfaces.py`。

## 2. MSS adapter

- `MSS_SOURCE_DIR` 只用于选择外部 MSS 资产目录；
- adapter 在启动 Octave 子进程时把它转换成 `MSS_ROOT` 环境变量；
- 没有 `sys.path` 注入，也没有导入其他仓库源码；
- 默认路径只在环境变量缺失时使用工作区相对布局，测试可通过环境变量覆盖；
- `tests/test_mss_remus100.py` 在完整环境下执行，不再跳过。

结论：PVS/MSS 环境变量契约保持不变，本 pilot 不修改 adapter。

## 3. import guard

- `tests/test_import_guard.py` 在隔离子进程中设置本仓库 `src` 的 `PYTHONPATH`，
  用于验证包导入不会加载 planner、simulator、ROS 或 Torch；
- 该设置只存在于测试子进程，不是生产运行路径；
- 生产代码没有新增 `sys.path`、动态 import 或跨仓库源码依赖；
- `scripts/check_repo_dependencies.py --root . --check` 返回 PASS。

结论：import 边界未退化；没有需要在本 pilot 修改的 adapter 代码。

## 4. 对 Step 3 的结论

planning、evaluation 和 experiments 的 manifest 写出已经收敛到同一个稳定 helper；
CSV/report 因语义不同保持原状；contracts 和 adapter 的只读审计未发现需要立即修改的
重复实现或越界依赖。REF-GLOBAL 可以关闭，剩余 CSV/report 和大模块拆分进入 G04。
