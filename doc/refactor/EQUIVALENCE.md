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
