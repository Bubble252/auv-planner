# auv-planner Equivalence Evidence

**状态**：`REF_GLOBAL_COMPLETE`<br>
**仓库**：`settled_全局规划器`<br>
**基线 commit**：`f606816`<br>
**日期**：2026-11-13

## 1. 候选 GLOBAL-A1

```yaml
goal: META-G03
candidate: GLOBAL-A1
repository: settled_全局规划器
base_commit: f606816
branch: refactor/global-20261113
files:
  - src/auv_planner/_json.py
  - src/auv_planner/evaluation/runner.py
public_api_change: none
```

GLOBAL-A1 只把 `evaluation/runner.py` 中已有的稳定 JSON 文档写出收敛到内部纯 helper：
`indent=2`、`sort_keys=True`、UTF-8、末尾单个换行。helper 不创建父目录、不改变
`write_run_log` 的父目录创建行为和返回路径。

| 项目 | 重构前 | 重构后 | 证据 |
|---|---|---|---|
| 文档文本 | `json.dump(..., indent=2, sort_keys=True)` + `"\\n"` | 同一文本一次渲染后写出 | 字节 fixture |
| 编码 | UTF-8 | UTF-8 | 文件读取测试 |
| 父目录 | `write_run_log` 创建 | 保持 | runner 测试 |
| 返回路径 | `Path` | 相同 | runner 测试 |
| 非 JSON 值 | 由 `json.dumps` 抛错 | 相同 | helper 负控 |
| RNG / 全局状态 | 不消耗/不修改 | 不变 | 纯函数检查 |

验证命令：

```bash
cd /home/bubble/水下机器人/settled_全局规划器/.worktrees/ref-global-20261113
/home/bubble/水下机器人/settled_全局规划器/.venv/bin/python \
  -m pytest -q tests/test_json_io.py tests/test_runner.py
```

Preflight 证据：

```yaml
skill_usage:
  - skill: auv-refactor-guard
    phase: preflight
    outcome: passed
    repo: /home/bubble/水下机器人/settled_全局规划器/.worktrees/ref-global-20261113
    module: src/auv_planner/evaluation/runner.py
```

- 候选 commit：`138265d`；测试 commit：`d1a8fd1`、`10f926b`；基线 commit：`da47735`；
- 针对性测试：`9 passed`；
- 全量测试：`97 passed`；
- ruff：helper、runner 和两个测试全部 PASS；
- format：四个改动文件全部 PASS；
- mypy：`3 errors / 2 files`，与基线一致，无新增类型错误；
- shape：`0 new violations, 119 suppressed`；
- dependency checker：`repository dependency boundaries: ok`；
- 字节等价：sorted keys、2-space indent、UTF-8、末尾单个换行由 fixture 测试锁定；
- 已知失败：无新增；
- 是否新增失败：`no`；
- 回滚 commit：`f606816`；
- 结论：`PASS`

## 2. 候选 GLOBAL-A2

```yaml
goal: META-G03
candidate: GLOBAL-A2
repository: settled_全局规划器
base_commit: 7242368
branch: refactor/global-20261113
files:
  - src/auv_planner/scene_catalog.py
public_api_change: none
```

GLOBAL-A2 把 `write_scene_catalog_manifest` 的 JSON 文档写出迁移到 GLOBAL-A1 的
helper。函数仍先创建父目录，再写 UTF-8 文件并返回 `Path`；manifest payload、字段、
排序、digest 和路径返回值都不变。

| 项目 | 重构前 | 重构后 | 证据 |
|---|---|---|---|
| 文档文本 | `json.dumps(..., indent=2, sort_keys=True) + "\n"` | 同一 helper | 字节 fixture |
| 父目录 | 创建 | 保持 | 临时目录测试 |
| 返回路径 | 输入路径的 `Path` | 相同 | 临时目录测试 |
| manifest schema | 不变 | 不变 | committed manifest 测试 |
| digest | 不变 | 不变 | catalog digest 测试 |

验证命令：

```bash
cd /home/bubble/水下机器人/settled_全局规划器/.worktrees/ref-global-20261113
/home/bubble/水下机器人/settled_全局规划器/.venv/bin/python \
  -m pytest -q tests/test_m5_scene_catalog.py
```

Preflight 证据：

```yaml
skill_usage:
  - skill: auv-refactor-guard
    phase: preflight
    outcome: passed
    repo: /home/bubble/水下机器人/settled_全局规划器/.worktrees/ref-global-20261113
    module: src/auv_planner/scene_catalog.py
```

- 候选 commit：`deb83dd`；测试 commit：`9c2fd62`；计划 commit：`113ae27`；
- 针对性测试：`9 passed`；
- 全量测试：`98 passed`；
- ruff：scene catalog、helper、catalog 测试和 JSON helper 测试全部 PASS；
- format：相关文件全部 PASS；
- mypy：`3 errors / 2 files`，与基线一致，无新增类型错误；
- shape：`0 new violations, 119 suppressed`；
- dependency checker：`repository dependency boundaries: ok`；
- 字节等价：catalog manifest 的 payload、排序、缩进、末尾换行和 digest 不变；
- 已知失败：无新增；
- 是否新增失败：`no`；
- 回滚 commit：`7242368`；
- 结论：`PASS`

## 3. 候选 GLOBAL-A3

```yaml
goal: META-G03
candidate: GLOBAL-A3
repository: settled_全局规划器
base_commit: 0d4c46b
branch: refactor/global-20261113
files:
  - src/auv_planner/experiments/m6_recovery.py
  - src/auv_planner/experiments/m7_budget.py
public_api_change: none
```

GLOBAL-A3 只迁移 M6 config manifest 和 M7 budget manifest 两个公开 writer 到同一个
稳定 JSON 文档 helper。两个 writer 仍先创建父目录，再写出 UTF-8 文件并返回 `Path`；
manifest payload、字段、排序、缩进和末尾换行保持不变。

| 项目 | 重构前 | 重构后 | 证据 |
|---|---|---|---|
| M6 manifest 字节 | `dumps(...)+ "\n"` | 同一 helper | 字节测试 |
| M7 manifest 字节 | `dumps(...)+ "\n"` | 同一 helper | 字节测试 |
| 父目录 | 创建 | 保持 | 临时目录测试 |
| 返回路径 | 输入路径的 `Path` | 相同 | 临时目录测试 |
| manifest schema | 不变 | 不变 | committed manifest 测试 |

验证命令：

```bash
cd /home/bubble/水下机器人/settled_全局规划器/.worktrees/ref-global-20261113
/home/bubble/水下机器人/settled_全局规划器/.venv/bin/python \
  -m pytest -q tests/test_recovery.py tests/test_recovery_query.py tests/test_json_io.py
```

Preflight 证据：

```yaml
skill_usage:
  - skill: auv-refactor-guard
    phase: preflight
    outcome: passed
    repo: /home/bubble/水下机器人/settled_全局规划器/.worktrees/ref-global-20261113
    module: src/auv_planner/experiments/m6_recovery.py
  - skill: auv-refactor-guard
    phase: preflight
    outcome: passed
    repo: /home/bubble/水下机器人/settled_全局规划器/.worktrees/ref-global-20261113
    module: src/auv_planner/experiments/m7_budget.py
```

- 候选 commit：`f9c6d16`；测试 commit：`5b34a08`；计划 commit：`8afc426`；
- shape 基线刷新：`d2a1331`；
- 针对性测试：`28 passed`；
- 全量测试：`100 passed`；
- ruff：两个 experiment 模块和两个测试全部 PASS；
- format：相关文件全部 PASS；
- mypy：`3 errors / 2 files`，与基线一致，无新增类型错误；
- shape：刷新 ratchet 后 `0 new violations, 119 suppressed`；
- dependency checker：`repository dependency boundaries: ok`；
- manifest 字节：M6/M7 payload、字段、排序、缩进和末尾换行均由测试锁定；
- 已知失败：无新增；
- 是否新增失败：`no`；
- 回滚 commit：`0d4c46b`；
- 结论：`PASS`

## 4. 候选 GLOBAL-A4

```yaml
goal: META-G04-CSV
candidate: GLOBAL-A4
repository: settled_全局规划器
base_commit: 4fe888e
branch: refactor/g04-csv-20261113
files:
  - src/auv_planner/_csv.py
  - src/auv_planner/experiments/m7_1.py
  - src/auv_planner/experiments/m7_2.py
  - tests/test_csv_writers.py
public_api_change: none
```

GLOBAL-A4 只合并 `m7_1.py` 与 `m7_2.py` 中字节等价的 CSV writer。两者都允许空
结果写空文件、使用第一行 key 作为 header、原样写出 list 值、不创建父目录，并使用
`newline=""`。M5/M6/M7 budget 和其他 report writer 保留原实现。

| 项目 | 重构前 | 重构后 | 证据 |
|---|---|---|---|
| 空 rows | 写空文件 | 相同 | `test_csv_writers.py` |
| 字段顺序 | 第一条记录 key | 相同 | 字节 fixture |
| 特殊字符/换行 | CSV 默认转义与 `\r\n` | 相同 | 字节 fixture |
| list 编码 | Python 字符串表示 | 相同 | 字节 fixture |
| 父目录 | 不创建 | 相同 | `FileNotFoundError` 测试 |
| 公共入口 | `_write_csv` 私有函数 | 保留兼容 wrapper | 导入与测试 |
| RNG / 全局状态 | 不消耗/不修改 | 不变 | 纯写出检查 |

Preflight 证据：

```yaml
skill_usage:
  - skill: auv-refactor-guard
    phase: preflight
    outcome: passed
    repo: /home/bubble/水下机器人/settled_全局规划器/.worktrees/ref-g04-csv-20261113
    module: src/auv_planner/experiments/m7_1.py
  - skill: auv-refactor-guard
    phase: preflight
    outcome: passed
    repo: /home/bubble/水下机器人/settled_全局规划器/.worktrees/ref-g04-csv-20261113
    module: src/auv_planner/experiments/m7_2.py
  - skill: auv-refactor-guard
    phase: preflight
    outcome: passed
    repo: /home/bubble/水下机器人/settled_全局规划器/.worktrees/ref-g04-csv-20261113
    module: src/auv_planner/_csv.py
```

- 测试 commit：`3826b38`、`4a78d54`；helper commit：`22e09aa`；source commit：`3fe93d4`；
- shape baseline refresh：`9419883`；
- 定向测试：`21 passed`；
- 全量测试：`108 passed`；
- ruff / format：改动文件 PASS；
- mypy：`3 errors / 2 files`，与基线一致；
- shape：刷新后 `0 new violations, 119 suppressed`；
- dependency checker：`repository dependency boundaries: ok`；
- 回滚 commit：`4fe888e`；
- 结论：`PASS`

## 5. 候选 GLOBAL-A5

```yaml
goal: META-G04-BIG1
candidate: GLOBAL-A5
repository: settled_全局规划器
base_commit: 923663e
branch: refactor/g04-big1-m71-20261113
files:
  - src/auv_planner/experiments/m7_1/types.py
  - src/auv_planner/experiments/m7_1/audit.py
  - src/auv_planner/experiments/m7_1/repair.py
  - src/auv_planner/experiments/m7_1/io.py
  - src/auv_planner/experiments/m7_1/runner.py
  - src/auv_planner/experiments/m7_1/__init__.py
  - tests/test_m7_1_golden.py
public_api_change: none
```

GLOBAL-A5 把原先约 1477 行的 `m7_1.py` 拆成 `types`、`audit`、`repair`、`io` 和
薄 `runner`。包级 `__init__.py` 只做兼容 re-export；`m7_2.py`、CLI、测试和
viz 继续使用原导入路径。拆分没有改变 case、planner、阈值、采样、repair 搜索、
CSV 字段/顺序、summary/manifest schema、reward、termination、success 或 seed。

| 项目 | 重构前 | 重构后 | 证据 |
|---|---|---|---|
| 公共入口 | `m7_1.py` 导出 | package `__init__.py` re-export | `test_m7_1.py`、`test_m7_2.py` |
| 私有兼容入口 | `_plan_request`、`_candidate_states`、`_write_csv` | 从实际实现模块 re-export | `test_m7_2.py`、`test_csv_writers.py` |
| 结果对象 | 字段和顺序不变 | 相同 | golden result signature |
| CSV/summary/manifest | 原 writer 输出 | 逐项字节等价 | `test_m7_1_golden.py` |
| 运行时间字段 | 不可字节比较 | 归一化 `<time>` | golden fixture |
| Git provenance | 提交后 `git_commit` 必变 | 归一化 `<commit>` | golden fixture |
| 文件规模 | `m7_1.py` 1477 行 | 最大模块约 442 行 | `wc -l` |

golden 首次运行时发现 `manifest.json` 的运行时 `hardware.git_commit` 被纳入字节哈希：
生成 fixture 时的 commit 为 `923663e`，提交 golden 后的 HEAD 为 `9f2633a`，导致
测试自失效。修复只把 `git_commit` 归一化为 `<commit>`，其余 manifest 字段仍参与
哈希；其他五个 artifact 的预期 SHA256 未改变。

验证命令：

```bash
cd /home/bubble/水下机器人/settled_全局规划器/.worktrees/ref-g04-big1-m71-20261113
/home/bubble/水下机器人/settled_全局规划器/.venv/bin/python -m pytest -q \
  tests/test_m7_1_golden.py tests/test_m7_1.py tests/test_m7_2.py tests/test_csv_writers.py
/home/bubble/水下机器人/settled_全局规划器/.venv/bin/python -m pytest -q tests
```

- 代码 commits：`6ed46ee`（types）、`b0b2313`（audit）、`49b1df7`（repair）、
  `cfc4b2d`（io）、`ae9e265`（shape ratchet）；
- golden 修复 commit：`3df0f14`；
- 定向测试：`22 passed`；
- 全量测试（不带 PVS/MSS）：`103 passed, 6 skipped`；
- 全量测试（完整 PVS/MSS）：`109 passed`；
- ruff / format：改动文件 PASS；
- mypy：`3 errors / 2 files`，与基线一致；
- shape：`0 new violations, 117 suppressed`；
- dependency checker：`repository dependency boundaries: ok`；
- 回滚 commit：`923663e`；
- 结论：`PASS`

## 6. 候选 G04-EXPERIMENTS-E1

```yaml
goal: META-G04-EXPERIMENTS
candidate: EXPERIMENTS-E1
repository: settled_全局规划器
base_commit: e55cf5f
branch: refactor/g04-experiments-20261114
implementation_commit: 9b4ac0c
files:
  - src/auv_planner/experiments/validation/closed_loop.py
  - src/auv_planner/experiments/validation/model_validation.py
  - src/auv_planner/experiments/validation/recovery.py
  - src/auv_planner/experiments/m4_closed_loop.py
  - src/auv_planner/experiments/m5_validation.py
  - src/auv_planner/experiments/m6_recovery.py
public_api_change: none
```

M4/M5/M6 归入 `experiments/validation/`。旧 `m*.py` 在 `sys.modules` 中指向新
模块对象，因此旧/新 import、公共对象身份和模块级 monkeypatch 保持同一命名空间。
全量测试 `111 passed`；定向契约测试验证模块身份和导出对象身份；shape
`0 new / 114 suppressed`；dependency `ok`。

## 7. 候选 G04-EXPERIMENTS-E2

```yaml
goal: META-G04-EXPERIMENTS
candidate: EXPERIMENTS-E2
repository: settled_全局规划器
base_commit: e55cf5f
branch: refactor/g04-experiments-20261114
implementation_commit: 87fda7f
files:
  - src/auv_planner/experiments/planner_bench/planner_comparison.py
  - src/auv_planner/experiments/planner_bench/budget.py
  - src/auv_planner/experiments/m7_2.py
  - src/auv_planner/experiments/m7_budget.py
public_api_change: none
```

M7.2 和 budget 归入 `experiments/planner_bench/`。`m7_2`、`m7_budget` 保留同一
模块对象别名。固定 CSV writer 测试、M7.2 artifact 测试和全量测试均通过；全量
`112 passed`；shape `0 new / 112 suppressed`；dependency `ok`。

## 8. 候选 G04-EXPERIMENTS-E3

```yaml
goal: META-G04-EXPERIMENTS
candidate: EXPERIMENTS-E3
repository: settled_全局规划器
base_commit: e55cf5f
branch: refactor/g04-experiments-20261114
implementation_commit: 62b8fe9
files:
  - src/auv_planner/experiments/planner_bench/path_audit/
  - src/auv_planner/experiments/m7_1/
public_api_change: none
```

M7.1 package 归入 `planner_bench/path_audit/`，旧 `m7_1` package 及五个子模块保留
兼容入口。`test_m7_1_golden.py` 的固定 case、CSV、summary、manifest 和 result
signature 全部通过；全量测试 `113 passed`；shape `0 new / 112 suppressed`；
dependency `ok`。E3 在 E1/E2 全部通过后执行。

## 9. G04-EXPERIMENTS golden 可移植性修复

```yaml
goal: META-G04-EXPERIMENTS
candidate: EXPERIMENTS-GOLDEN-PORTABILITY
repository: settled_全局规划器
branch: fix/g04-golden-portability-20261114
followup_branch: fix/g04-golden-float-20261114
base_commit: 0ec8c4a
files:
  - tests/test_m7_1_golden.py
public_api_change: none
```

服务器同步验证发现两处不可移植性：

1. `manifest.json` 的归一化只屏蔽运行时间和 commit，但仍把 `hardware` 中的
   hostname、CPU 数量、BLAS 配置和 Python 路径纳入哈希；
2. 轨迹 CSV 保留浮点末位，同一算法在不同 BLAS/CPU 上出现约 `1e-16` 的差异。

修复只触及测试：整个 `hardware` 块归一化为 `<hardware>`；CSV 数值统一格式化为
12 位小数；更新对应的期望哈希。算法、字段、artifact schema 和运行行为不变。

本地与服务器使用相同归一化后，六个 golden 文件 SHA256 全部一致：

| 文件 | SHA256 |
|---|---|
| `manifest.json` | `99c9898320a8664cd5c4d18e4afab3ba053fdb7e2cdf133adf8a347328f67992` |
| `paths.csv` | `36794362e7ef6b4b3754e64ac70663126d9269484c805b5234d781588c8505f6` |
| `points.csv` | `4ba82f5da234ba8ccd4f64251dd19cda7f8fda47da5c8a6e4e1052045d5e4f1e` |
| `repair_attempts.csv` | `7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6` |
| `summary.json` | `9ad13fda85d478b82acdcb534028f99ae62927f7efb5ef08e9972e83f3a02b7c` |
| `trajectories.csv` | `77b418d006474c2b6028a8d1eedfde5e4271ed34488dd85d3c8709eacb201a0a` |

定向测试 `12 passed`；全量测试 `115 passed`；shape `0 new / 0 suppressed`；
dependency `ok`；ruff 与 format PASS。
