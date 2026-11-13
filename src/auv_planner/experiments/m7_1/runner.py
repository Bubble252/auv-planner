from __future__ import annotations

from pathlib import Path
from time import perf_counter

from ...evaluation.runner import EvaluationRecord, run_scenario
from ...planners.astar import AStarPlanner
from ...planners.rrt_star import RRTStarPlanner
from ..m7_budget import m7_probes
from .audit import _failed_path_audit, audit_trajectory
from .io import _write_outputs
from .repair import _attempt_repair
from .types import (
    AuditPoint,
    M71CaseResult,
    M71CaseSpec,
    M71Config,
    M71ExperimentResult,
    PathAudit,
    RepairAttempt,
)


def m71_case_specs(config: M71Config | None = None) -> tuple[M71CaseSpec, ...]:
    active = M71Config() if config is None else config
    selected = None if active.case_names is None else set(active.case_names)
    probes = [
        M71CaseSpec(
            name=probe.name,
            scenario=probe.scenario,
            safe_anchor_ned_m=probe.safe_anchor_ned_m,
            include_in_aggregate=probe.include_in_aggregate,
        )
        for probe in m7_probes()
    ]
    if selected is not None:
        known = {probe.name for probe in probes}
        missing = selected - known
        if missing:
            raise ValueError(f"unknown M7.1 cases: {sorted(missing)}")
        probes = [probe for probe in probes if probe.name in selected]
    return tuple(probes)


def _planner(name: str, config: M71Config) -> AStarPlanner | RRTStarPlanner:
    if name == "astar":
        return AStarPlanner(
            resolution_m=config.astar_resolution_m,
            timeout_s=config.astar_timeout_s,
            collision_step_m=0.1,
        )
    if name == "rrt_star":
        return RRTStarPlanner(
            step_size_m=config.rrt_step_size_m,
            max_iterations=config.rrt_iterations,
            timeout_s=config.rrt_timeout_s,
            collision_step_m=0.1,
        )
    raise ValueError(f"unknown planner: {name}")


def run_m7_1(output_dir: Path | str, config: M71Config | None = None) -> M71ExperimentResult:
    active = M71Config() if config is None else config
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    started = perf_counter()
    cases: list[M71CaseResult] = []
    specs = m71_case_specs(active)
    for spec in specs:
        for planner_name in active.planner_names:
            planner = _planner(planner_name, active)
            record: EvaluationRecord = run_scenario(spec.scenario, planner, seed=active.seed)
            if record.plan.trajectory is None:
                baseline = _failed_path_audit(
                    case_name=spec.name,
                    scenario=spec.scenario,
                    planner_name=planner_name,
                    include_in_aggregate=spec.include_in_aggregate,
                    plan=record.plan,
                    config=active,
                )
                repair = None
                attempts: tuple[RepairAttempt, ...] = ()
                accepted = False
                repair_reason = "baseline_plan_failed"
            else:
                baseline = audit_trajectory(
                    record.plan.trajectory,
                    spec.scenario,
                    case_name=spec.name,
                    planner_name=planner_name,
                    variant="baseline",
                    include_in_aggregate=spec.include_in_aggregate,
                    plan_status=record.plan.status.value,
                    plan_success=record.result.success,
                    plan_reason=record.plan.reason,
                    planning_time_s=record.plan.planning_time_s,
                    repair_time_s=0.0,
                    config=active,
                    safe_anchor_ned_m=spec.safe_anchor_ned_m,
                )
                repair, attempts, _, accepted, repair_reason = _attempt_repair(
                    baseline,
                    spec.scenario,
                    spec,
                    active,
                )
            cases.append(
                M71CaseResult(
                    case_name=spec.name,
                    scenario_name=spec.scenario.name,
                    planner_name=planner_name,
                    include_in_aggregate=spec.include_in_aggregate,
                    baseline=baseline,
                    repair=repair,
                    repair_attempts=attempts,
                    repair_accepted=accepted,
                    repair_reason=repair_reason,
                )
            )
    result = M71ExperimentResult(
        config=active,
        cases=tuple(cases),
        elapsed_s=perf_counter() - started,
    )
    _write_outputs(root, result)
    return result


__all__ = [
    "AuditPoint",
    "M71CaseResult",
    "M71CaseSpec",
    "M71Config",
    "M71ExperimentResult",
    "PathAudit",
    "RepairAttempt",
    "audit_trajectory",
    "m71_case_specs",
    "run_m7_1",
]
