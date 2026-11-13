# auv-planner Equivalence Evidence

**状态**：`REF_GLOBAL_INVENTORY_COMPLETE`<br>
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
