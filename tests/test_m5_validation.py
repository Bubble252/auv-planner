from __future__ import annotations

import shutil
from typing import Any

import pytest

from auv_planner.dynamics.mss_remus100 import _default_mss_source_dir
from auv_planner.experiments.m5_validation import (
    proposed_model_thresholds,
    run_derivative_comparison,
)

MSS_AVAILABLE = shutil.which("octave") is not None and _default_mss_source_dir().is_dir()


@pytest.mark.skipif(
    not MSS_AVAILABLE,
    reason="Octave and the local MSS tree are required for the model comparison",
)
def test_m5_derivative_differences_stay_within_audited_model_bands() -> None:
    rows: dict[str, dict[str, Any]] = {str(row["case"]): row for row in run_derivative_comparison()}
    calm = ("calm_straight", "calm_rudder", "calm_stern_plane", "combined_attitude")
    for name in calm:
        assert float(rows[name]["relative_l2"]) < 0.07
    assert float(rows["depth_shear"]["relative_l2"]) < 0.07
    assert float(rows["cross_current"]["relative_l2"]) < 0.35


def test_m5_thresholds_are_frozen_project_acceptance_thresholds() -> None:
    thresholds = proposed_model_thresholds()
    assert thresholds["constraint_violations_max"] == 0.0
    assert "frozen" in str(thresholds["status"])
    assert "not industry standards" in str(thresholds["status"])
