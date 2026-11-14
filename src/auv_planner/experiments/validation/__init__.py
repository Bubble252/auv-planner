"""Stable imports for model-validation and recovery experiments.

Non-responsibility: does not implement experiment logic or modify public
artifact schemas.
"""

from .closed_loop import M4Case, m4_cases, run_m4_suite
from .model_validation import (
    ClosedLoopCase,
    OpenLoopCase,
    OpenLoopTrace,
    build_threshold_audit,
    closed_loop_cases,
    compare_traces,
    derivative_cases,
    model_trace_metrics,
    open_loop_cases,
    run_closed_loop_comparison,
    run_derivative_comparison,
    run_m5_validation,
    run_mass_density_sensitivity,
    run_open_loop_comparison,
    run_open_loop_trace,
    run_step_convergence,
)
from .recovery import (
    M6ConstraintVariant,
    M6KeyNode,
    dead_end_scene,
    m6_config_manifest,
    m6_constraint_variants,
    m6_key_nodes,
    run_m6_recovery,
    write_m6_config_manifest,
)

__all__ = [
    "ClosedLoopCase",
    "M4Case",
    "M6ConstraintVariant",
    "M6KeyNode",
    "OpenLoopCase",
    "OpenLoopTrace",
    "build_threshold_audit",
    "closed_loop_cases",
    "compare_traces",
    "dead_end_scene",
    "derivative_cases",
    "m4_cases",
    "m6_config_manifest",
    "m6_constraint_variants",
    "m6_key_nodes",
    "model_trace_metrics",
    "open_loop_cases",
    "run_closed_loop_comparison",
    "run_derivative_comparison",
    "run_m4_suite",
    "run_m5_validation",
    "run_m6_recovery",
    "run_mass_density_sensitivity",
    "run_open_loop_comparison",
    "run_open_loop_trace",
    "run_step_convergence",
    "write_m6_config_manifest",
]
