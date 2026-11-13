# auv-planner Refactor Baseline

**状态**：`REF_GLOBAL_INVENTORY_COMPLETE`<br>
**仓库**：`settled_全局规划器`<br>
**基线 commit**：`f606816`<br>
**日期**：2026-11-13

## 1. 运行环境

```bash
cd /home/bubble/水下机器人/settled_全局规划器/.worktrees/ref-global-20261113
export PVS_SOURCE_DIR=/home/bubble/水下机器人/python/PythonVehicleSimulator-master/src
export MSS_SOURCE_DIR=/home/bubble/水下机器人/simulator/MSS-master
```

测试使用仓库自己的虚拟环境
`/home/bubble/水下机器人/settled_全局规划器/.venv/bin/python`。linked worktree 中没有
`.venv`，所以必须使用绝对路径；该环境已 editable 安装 `auv-core`。

## 2. 测试与检查

| 检查 | 命令 | 基线 |
|---|---|---|
| pytest（完整环境） | `.venv/bin/python -m pytest -q tests` | `92 passed`，27.49s |
| pytest（无 PVS/MSS/Octave） | 同上，不设置环境变量 | `86 passed, 6 skipped` |
| ruff | `.venv/bin/python -m ruff check src tests scripts` | 45 个存量错误；候选文件必须为 0 新增 |
| format | `.venv/bin/python -m ruff format --check src tests scripts` | 7 个文件待格式化；候选文件必须通过 |
| mypy | 根 `.venv/bin/python -m mypy --config-file pyproject.toml` | 3 errors / 2 files；候选文件不得新增 |
| shape | `总协调/scripts/check_code_shape.py --root . --check` | `0 new / 119 suppressed` |
| dependency | `scripts/check_repo_dependencies.py --root . --check` | PASS |
| import guard | `tests/test_import_guard.py` | PASS |

仓库自己的 `.venv` 没有安装 mypy，因此 mypy 使用工作区根虚拟环境；运行目录仍是
本仓库根目录，不能把根环境用于 pytest。

## 3. 已知跳过

不设置 `PVS_SOURCE_DIR` / `MSS_SOURCE_DIR` 时，6 个 MSS/Octave 对比测试会跳过；
设置后全部执行并通过。跳过不是通过，候选验收以完整环境下的 92 项为准。

## 4. 已知欠账

- ruff 45 errors 和 7 个未格式化文件是历史基线，不在候选 commit 中整仓清理；
- mypy 3 个 `unused-ignore` 是历史类型检查欠账，不通过关闭检查或增加 ignore 修复；
- `m7_1.py`、`planners/recoverable.py`、`m5_validation.py`、`m7_budget.py` 和
  `m7_2.py` 超过新代码硬上限，只进入 shape ratchet，不在 pilot 中整文件重写；
- `scripts/render_*` 的导入顺序和格式欠账与核心评价/实验入口分离，后续单独候选。

## 5. 回滚点

- 基线 commit：`f606816`；
- 候选失败时使用 `git revert <candidate-commit>`，不在主干上 `reset --hard`；
- 回滚后重新运行完整环境测试、ruff（改动文件）、shape 和依赖边界检查。
