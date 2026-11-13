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

- 结果：`PENDING`
