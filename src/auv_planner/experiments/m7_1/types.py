"""Configuration and result models shared by the M7.1 experiment modules."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from auv_core.contracts import FloatArray, ScenarioConfig, Trajectory

from ...recovery import FaultProfile, RecoveryQueryStatus, fault_profile_by_name

M71_AUDIT_INTERVAL_S = 1.0
M71_ONLINE_BUDGET_S = 10.0


@dataclass(frozen=True)
class M71Config:
    audit_interval_s: float = M71_AUDIT_INTERVAL_S
    online_budget_s: float = M71_ONLINE_BUDGET_S
    profile_name: str = "P1_degraded"
    full_workers: int = 8
    seed: int = 0
    astar_resolution_m: float = 0.5
    astar_timeout_s: float = 10.0
    rrt_step_size_m: float = 0.6
    rrt_iterations: int = 2_000
    rrt_timeout_s: float = 3.0
    repair_offsets_m: tuple[float, ...] = (1.0, 1.6, 2.2)
    max_repair_candidates: int = 12
    case_names: tuple[str, ...] | None = None
    planner_names: tuple[str, ...] = ("astar", "rrt_star")

    def __post_init__(self) -> None:
        if not np.isfinite(self.audit_interval_s) or self.audit_interval_s <= 0.0:
            raise ValueError("audit_interval_s must be finite and positive")
        if self.audit_interval_s > 1.0:
            raise ValueError("audit_interval_s must not exceed 1 s")
        if not np.isfinite(self.online_budget_s) or self.online_budget_s <= 0.0:
            raise ValueError("online_budget_s must be finite and positive")
        if not self.profile_name:
            raise ValueError("profile_name must not be empty")
        if not isinstance(self.full_workers, int) or self.full_workers < 1:
            raise ValueError("full_workers must be a positive integer")
        if not isinstance(self.seed, int) or self.seed < 0:
            raise ValueError("seed must be a non-negative integer")
        for name in (
            "astar_resolution_m",
            "astar_timeout_s",
            "rrt_step_size_m",
            "rrt_timeout_s",
        ):
            value = getattr(self, name)
            if not np.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        if not isinstance(self.rrt_iterations, int) or self.rrt_iterations < 1:
            raise ValueError("rrt_iterations must be a positive integer")
        if not self.repair_offsets_m or any(
            not np.isfinite(value) or value <= 0.0 for value in self.repair_offsets_m
        ):
            raise ValueError("repair_offsets_m must contain positive finite values")
        if not isinstance(self.max_repair_candidates, int) or self.max_repair_candidates < 0:
            raise ValueError("max_repair_candidates must be a non-negative integer")
        if self.case_names is not None:
            if not self.case_names or any(not name for name in self.case_names):
                raise ValueError("case_names must be a non-empty sequence of names")
            object.__setattr__(self, "case_names", tuple(self.case_names))
        if not self.planner_names or any(
            name not in {"astar", "rrt_star"} for name in self.planner_names
        ):
            raise ValueError("planner_names must contain astar and/or rrt_star")
        object.__setattr__(self, "planner_names", tuple(self.planner_names))
        object.__setattr__(self, "repair_offsets_m", tuple(float(v) for v in self.repair_offsets_m))

    @property
    def profile(self) -> FaultProfile:
        return fault_profile_by_name(self.profile_name)


@dataclass(frozen=True)
class M71CaseSpec:
    name: str
    scenario: ScenarioConfig
    safe_anchor_ned_m: FloatArray | None
    include_in_aggregate: bool


@dataclass(frozen=True)
class AuditPoint:
    index: int
    t_s: float
    position_ned_m: FloatArray
    quat_xyzw: FloatArray
    clearance_m: float
    prefilter_reason: str | None
    online_status: str
    online_reason: str | None
    online_elapsed_s: float
    online_early_stopped: bool
    online_evaluated_checks: int
    full_status: str
    full_reason: str | None
    full_elapsed_s: float
    full_early_stopped: bool
    full_evaluated_checks: int
    certificate_valid_from_s: float | None
    certificate_valid_until_s: float | None
    failure_source: str | None


@dataclass(frozen=True)
class PathAudit:
    case_name: str
    scenario_name: str
    planner_name: str
    variant: str
    include_in_aggregate: bool
    plan_status: str
    plan_success: bool
    plan_reason: str | None
    planning_time_s: float
    repair_time_s: float
    trajectory: Trajectory | None
    points: tuple[AuditPoint, ...]
    prefilter_time_s: float
    online_time_s: float
    full_time_s: float
    path_length_m: float
    duration_s: float
    min_clearance_m: float
    coverage_ratio: float
    max_uncovered_s: float
    coverage_intervals: tuple[tuple[float, float], ...]
    uncovered_intervals: tuple[tuple[float, float], ...]
    failure_sources: tuple[tuple[str, int], ...]

    @property
    def valid_points(self) -> int:
        return sum(point.full_status == RecoveryQueryStatus.VALID.value for point in self.points)

    @property
    def invalid_points(self) -> int:
        return sum(point.full_status == RecoveryQueryStatus.INVALID.value for point in self.points)

    @property
    def unknown_points(self) -> int:
        return sum(point.full_status == RecoveryQueryStatus.UNKNOWN.value for point in self.points)

    @property
    def end_to_end_s(self) -> float:
        return self.planning_time_s + self.prefilter_time_s + self.online_time_s

    @property
    def full_end_to_end_s(self) -> float:
        return self.end_to_end_s + self.full_time_s


@dataclass(frozen=True)
class RepairAttempt:
    candidate_index: int
    source: str
    via_ned_m: FloatArray | None
    candidate_status: str | None
    geometric_safe: bool
    plan_success: bool
    coverage_ratio: float
    max_uncovered_s: float
    accepted: bool
    reason: str


@dataclass(frozen=True)
class M71CaseResult:
    case_name: str
    scenario_name: str
    planner_name: str
    include_in_aggregate: bool
    baseline: PathAudit
    repair: PathAudit | None
    repair_attempts: tuple[RepairAttempt, ...]
    repair_accepted: bool
    repair_reason: str


@dataclass(frozen=True)
class M71ExperimentResult:
    config: M71Config
    cases: tuple[M71CaseResult, ...]
    elapsed_s: float


__all__ = [
    "AuditPoint",
    "M71CaseResult",
    "M71CaseSpec",
    "M71Config",
    "M71ExperimentResult",
    "PathAudit",
    "RepairAttempt",
]
