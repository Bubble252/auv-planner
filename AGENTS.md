# auv-planner 项目规则

本仓库是独立 Git 仓库 `/home/bubble/水下机器人/settled_全局规划器`，只承载全局规划器。

## 边界

- Python 包名：`auv_planner`；发行名：`auv-planner`。
- 只允许依赖 `auv-core`；不得导入 `auv_local`、`auv_rl`、`auv_lowlevel` 或
  `auv_isaaclab`。
- 不得通过 `../settled_全局规划器/src` 或其他仓库源码路径补依赖。
- `configs/`、`scripts/` 和 `src/` 中的共享契约必须来自已安装的 `auv-core`。

## 安装与测试

```bash
uv venv .venv
uv pip install --python .venv/bin/python -e /home/bubble/水下机器人/settled_共享基础
uv pip install --python .venv/bin/python numpy pytest plotly matplotlib
uv pip install --python .venv/bin/python --no-deps -e .
PVS_SOURCE_DIR=/home/bubble/水下机器人/python/PythonVehicleSimulator-master/src \
MSS_SOURCE_DIR=/home/bubble/水下机器人/simulator/MSS-master \
.venv/bin/python -m pytest -q
```

## Git

- 禁止 `git add -A`；只 add 明确文件。
- 不提交 `.venv/`、`artifacts/`、`outputs/`、日志、缓存和 checkpoint。
- 提交前运行 `git diff --cached --check`；不自动 commit / push，除非用户明确要求。

## 重构交接

重构基线、候选、允许目录和 G04 边界以 `doc/refactor/` 为准：

- `BASELINE.md`：环境、测试命令和已知 lint/type 欠账；
- `INVENTORY.md`：重复实现、CSV 审计结论和 G04 候选；
- `MODULE_MAP.md`：模块职责、非职责和冻结 manifest；
- `EQUIVALENCE.md`：GLOBAL-A1 至 GLOBAL-A3 的字节等价证据；
- `CSV_AUDIT.md`、`BOUNDARY_AUDIT.md`：只读审计结论。

完整功能验证：

```bash
export PVS_SOURCE_DIR=/home/bubble/水下机器人/python/PythonVehicleSimulator-master/src
export MSS_SOURCE_DIR=/home/bubble/水下机器人/simulator/MSS-master
/home/bubble/水下机器人/settled_全局规划器/.venv/bin/python -m pytest -q tests
/home/bubble/水下机器人/.venv/bin/python -m ruff check <changed-files>
/home/bubble/水下机器人/.venv/bin/python -m ruff format --check <changed-files>
/home/bubble/水下机器人/.venv/bin/python -m mypy --config-file pyproject.toml
```

仓库 `.venv` 没有 ruff；lint/format 使用工作区根环境，运行目录仍是本仓库根目录。
M5/M6/M7 manifest、seed/scene、评价协议和 planner 证书不得由 G04 自动改写。
