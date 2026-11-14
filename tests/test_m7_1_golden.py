from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any

from auv_planner.experiments.m7_1 import M71Config, run_m7_1

RUNTIME_TIME_KEYS = {
    "elapsed_s",
    "end_to_end_s",
    "full_end_to_end_s",
    "full_elapsed_s",
    "full_time_s",
    "online_elapsed_s",
    "online_time_s",
    "planning_time_s",
    "prefilter_time_s",
    "repair_time_s",
    "time_share_of_full_end_to_end",
}
EXPECTED_FILES = {
    "manifest.json",
    "paths.csv",
    "points.csv",
    "repair_attempts.csv",
    "summary.json",
    "trajectories.csv",
}
EXPECTED_SHA256 = {
    "manifest.json": "99c9898320a8664cd5c4d18e4afab3ba053fdb7e2cdf133adf8a347328f67992",
    "paths.csv": "36794362e7ef6b4b3754e64ac70663126d9269484c805b5234d781588c8505f6",
    "points.csv": "4ba82f5da234ba8ccd4f64251dd19cda7f8fda47da5c8a6e4e1052045d5e4f1e",
    "repair_attempts.csv": "7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6",
    "summary.json": "9ad13fda85d478b82acdcb534028f99ae62927f7efb5ef08e9972e83f3a02b7c",
    "trajectories.csv": "77b418d006474c2b6028a8d1eedfde5e4271ed34488dd85d3c8709eacb201a0a",
}


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: (
                "<hardware>"
                if key == "hardware"
                else "<time>"
                if key in RUNTIME_TIME_KEYS
                else "<commit>"
                if key == "git_commit"
                else _normalize(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return value


def _normalized_csv_bytes(path: Path) -> bytes:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    fieldnames = list(rows[0]) if rows else []
    normalized = [
        {
            key: ("<time>" if key in RUNTIME_TIME_KEYS else _normalize_csv_value(value))
            for key, value in row.items()
        }
        for row in rows
    ]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(normalized)
    return buffer.getvalue().encode()


def _normalize_csv_value(value: str) -> str:
    try:
        numeric = float(value)
    except ValueError:
        return value
    if not math.isfinite(numeric):
        return value
    return f"{numeric:.12f}"


def _normalized_bytes(path: Path) -> bytes:
    if path.suffix == ".csv":
        return _normalized_csv_bytes(path)
    if path.suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return (json.dumps(_normalize(payload), indent=2, sort_keys=True) + "\n").encode()
    return path.read_bytes()


def test_golden_normalization_masks_host_hardware() -> None:
    assert _normalize({"hardware": {"hostname": "host-a", "cpu_count": 32}}) == {
        "hardware": "<hardware>"
    }


def test_golden_normalization_collapses_float_tail() -> None:
    assert _normalize_csv_value("0.26201381142015484") == "0.262013811420"


def test_m7_1_golden_artifacts_and_result_signature(tmp_path: Path) -> None:
    config = M71Config(
        profile_name="P0_nominal",
        case_names=("open_water_start",),
        planner_names=("astar",),
        full_workers=1,
        max_repair_candidates=0,
    )

    result = run_m7_1(tmp_path, config)

    assert {path.name for path in tmp_path.iterdir() if path.is_file()} == EXPECTED_FILES
    for name, expected in EXPECTED_SHA256.items():
        assert hashlib.sha256(_normalized_bytes(tmp_path / name)).hexdigest() == expected
    assert [(case.case_name, case.planner_name, case.repair_reason) for case in result.cases] == [
        ("open_water_start", "astar", "no_repair_candidates")
    ]
    assert [len(case.baseline.points) for case in result.cases] == [14]
    assert [round(case.baseline.coverage_ratio, 12) for case in result.cases] == [0.970423728981]
