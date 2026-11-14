from __future__ import annotations

import importlib

import auv_planner.experiments as experiments


def test_validation_aliases_preserve_module_and_type_identity() -> None:
    aliases = {
        "m4_closed_loop": "validation.closed_loop",
        "m5_validation": "validation.model_validation",
        "m6_recovery": "validation.recovery",
        "m7_2": "planner_bench.planner_comparison",
        "m7_budget": "planner_bench.budget",
    }
    for old_name, new_name in aliases.items():
        old = importlib.import_module(f"auv_planner.experiments.{old_name}")
        new = importlib.import_module(f"auv_planner.experiments.{new_name}")
        assert old is new

        for public_name in old.__all__:
            assert getattr(old, public_name) is getattr(new, public_name)


def test_experiments_package_uses_validation_implementations() -> None:
    from auv_planner.experiments.validation.closed_loop import M4Case
    from auv_planner.experiments.validation.recovery import M6KeyNode

    assert experiments.M4Case is M4Case
    assert experiments.M6KeyNode is M6KeyNode


def test_experiments_package_uses_planner_bench_implementations() -> None:
    from auv_planner.experiments.planner_bench.budget import M7Probe
    from auv_planner.experiments.planner_bench.planner_comparison import M72Config

    assert experiments.M7Probe is M7Probe
    assert experiments.M72Config is M72Config
