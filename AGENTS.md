# auv-planner 项目规则

本仓库是独立 Git 仓库 `/home/bubble/水下机器人/settled_全局规划器`，只承载全局规划器。

## 边界

- Python 包名：`auv_planner`；发行名：`auv-planner`。
- 只允许依赖 `auv-core`；不得导入 `auv_local`、`auv_rl`、`auv_lowlevel` 或
  `auv_isaaclab`。
- 不得通过 `../settled_全局规划器/src` 或其他仓库源码路径补依赖。
- `configs/`、`scripts/` 和 `src/` 中的共享契约必须来自已安装的 `auv-core`。

## 治理入口

- 工作区规则：`/home/bubble/水下机器人/AGENTS.md`；
- canonical 代码规范：`/home/bubble/水下机器人/总协调/doc/governance/CODE_STYLE.md`；
- 接口与单位契约：`/home/bubble/水下机器人/总协调/doc/governance/CODE_INTERFACE_CONTRACT.md`；
- Goal 模板：`/home/bubble/水下机器人/总协调/doc/goals/GOAL_TEMPLATE.md`；
- experiment matrix schema：`/home/bubble/水下机器人/总协调/configs/governance/experiment_matrix.schema.json`。

本仓库当前没有 Goal front matter 或 canonical matrix；现有
`configs/experiments/m7_2.json` 继续作为冻结实验配置，不在 META-G01 中重写。
新 Goal 必须使用 canonical 模板；若实验轴不是 `levels × radii` 的局部评价形状，
先在 Goal 中登记 schema waiver，不得伪造 axes。

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
