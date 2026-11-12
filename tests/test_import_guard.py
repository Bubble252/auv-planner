from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _run_import_check(code: str) -> subprocess.CompletedProcess[str]:
    repo = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo / "src")
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _assert_clean(code: str) -> None:
    result = _run_import_check(code)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"


def test_core_import_does_not_load_simulator_ros_or_torch() -> None:
    _assert_clean(
        "import sys\n"
        "import auv_planner\n"
        "forbidden = {'holoocean', 'rclpy', 'torch', 'python_vehicle_simulator', "
        "'auv_core.contracts', 'auv_planner.control', 'auv_core.guidance', "
        "'auv_planner.planners', 'auv_core.dynamics.remus100'}\n"
        "loaded = forbidden.intersection(sys.modules)\n"
        "if loaded:\n"
        "    raise SystemExit(sorted(loaded))\n"
        "print('ok')\n"
    )


def test_contract_import_does_not_load_guidance_or_planners() -> None:
    _assert_clean(
        "import sys\n"
        "import auv_core.contracts\n"
        "forbidden = {'holoocean', 'rclpy', 'torch', 'python_vehicle_simulator', "
        "'auv_planner.control', 'auv_core.current', 'auv_core.geometry', "
        "'auv_core.guidance', 'auv_planner.interfaces', 'auv_planner.metrics', "
        "'auv_planner.planners', 'auv_core.scenarios', 'auv_core.dynamics.remus100'}\n"
        "loaded = forbidden.intersection(sys.modules)\n"
        "if loaded:\n"
        "    raise SystemExit(sorted(loaded))\n"
        "print('ok')\n"
    )


def test_guidance_import_does_not_load_planners_or_simulator() -> None:
    _assert_clean(
        "import sys\n"
        "import auv_core.guidance\n"
        "forbidden = {'python_vehicle_simulator', 'auv_planner.control', "
        "'auv_planner.planners', 'auv_core.dynamics.remus100'}\n"
        "loaded = forbidden.intersection(sys.modules)\n"
        "if loaded:\n"
        "    raise SystemExit(sorted(loaded))\n"
        "print('ok')\n"
    )


def test_public_exports_remain_lazily_available() -> None:
    _assert_clean(
        "import sys\n"
        "from auv_planner import State, ThreeDAlosGuidance\n"
        "assert State.__name__ == 'State'\n"
        "assert ThreeDAlosGuidance.__name__ == 'ThreeDAlosGuidance'\n"
        "assert 'auv_planner.planners' not in sys.modules\n"
        "print('ok')\n"
    )
