from __future__ import annotations

import csv
import hashlib
import io
import json
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
    "manifest.json": "9babfb970d80cb7274ea50215a8a43da13fe7ebe0c54b748dd5472943c2e219d",
    "paths.csv": "6436949885be4f165eb061164633d379931592d5225efec67276420030f39062",
    "points.csv": "64308d1ad77cd137a32eec2dbda30f910d65e8f8dd2c3596f3394a212b6bcb96",
    "repair_attempts.csv": "7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6",
    "summary.json": "9ad13fda85d478b82acdcb534028f99ae62927f7efb5ef08e9972e83f3a02b7c",
    "trajectories.csv": "46e9e30b7a70dd8bd663ecbe16d37d83210bc1a0e36d00a3c9ae04af37a15a45",
}


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: (
                "<time>"
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
        {key: ("<time>" if key in RUNTIME_TIME_KEYS else value) for key, value in row.items()}
        for row in rows
    ]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(normalized)
    return buffer.getvalue().encode()


def _normalized_bytes(path: Path) -> bytes:
    if path.suffix == ".csv":
        return _normalized_csv_bytes(path)
    if path.suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return (json.dumps(_normalize(payload), indent=2, sort_keys=True) + "\n").encode()
    return path.read_bytes()


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
