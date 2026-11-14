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


def test_m7_1_package_and_submodules_alias_path_audit() -> None:
    aliases = {
        "m7_1.audit": "planner_bench.path_audit.audit",
        "m7_1.io": "planner_bench.path_audit.io",
        "m7_1.repair": "planner_bench.path_audit.repair",
        "m7_1.runner": "planner_bench.path_audit.runner",
        "m7_1.types": "planner_bench.path_audit.types",
    }
    for old_name, new_name in aliases.items():
        old = importlib.import_module(f"auv_planner.experiments.{old_name}")
        new = importlib.import_module(f"auv_planner.experiments.{new_name}")
        assert old is new

    old_package = importlib.import_module("auv_planner.experiments.m7_1")
    new_package = importlib.import_module("auv_planner.experiments.planner_bench.path_audit")
    for public_name in old_package.__all__:
        assert getattr(old_package, public_name) is getattr(new_package, public_name)

    from auv_planner.experiments.m7_1 import M71Config, _plan_request
    from auv_planner.experiments.planner_bench.path_audit import (
        M71Config as PathAuditM71Config,
    )
    from auv_planner.experiments.planner_bench.path_audit import (
        _plan_request as path_audit_plan_request,
    )

    assert M71Config is PathAuditM71Config
    assert _plan_request is path_audit_plan_request
