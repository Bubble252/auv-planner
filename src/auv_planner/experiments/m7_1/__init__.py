"""Compatibility surface for the historical M7.1 audit package.

Non-responsibility: does not duplicate audit, repair, I/O, or runner logic.
"""

from __future__ import annotations

from ..planner_bench.path_audit import (
    AuditPoint,
    M71CaseResult,
    M71CaseSpec,
    M71Config,
    M71ExperimentResult,
    PathAudit,
    RepairAttempt,
    _candidate_states,
    _plan_request,
    _write_csv,
    audit_trajectory,
    coverage_metrics,
    m71_case_specs,
    run_m7_1,
    sample_trajectory_states,
)

__all__ = [
    "AuditPoint",
    "M71CaseResult",
    "M71CaseSpec",
    "M71Config",
    "M71ExperimentResult",
    "PathAudit",
    "RepairAttempt",
    "audit_trajectory",
    "coverage_metrics",
    "m71_case_specs",
    "run_m7_1",
    "sample_trajectory_states",
]
