from __future__ import annotations

import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from ..._csv import write_csv_allow_empty
from ...evaluation.runner import EvaluationRecord, run_scenario
from ...planners.astar import AStarPlanner
from ...planners.rrt_star import RRTStarPlanner
from ..m7_budget import hardware_manifest, m7_probes
from .audit import _failed_path_audit, audit_trajectory
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


def _write_outputs(root: Path, result: M71ExperimentResult) -> None:
    _write_paths_csv(root / "paths.csv", result.cases)
    _write_points_csv(root / "points.csv", result.cases)
    _write_trajectories_csv(root / "trajectories.csv", result.cases)
    _write_repair_attempts_csv(root / "repair_attempts.csv", result.cases)
    _write_summary(root / "summary.json", result)
    _write_manifest(root / "manifest.json", result)


def _write_paths_csv(path: Path, cases: Sequence[M71CaseResult]) -> None:
    rows: list[dict[str, Any]] = []
    for case in cases:
        repair_variant = "repair_accepted" if case.repair_accepted else "repair_attempt"
        for audit, variant in ((case.baseline, "baseline"), (case.repair, repair_variant)):
            if audit is None:
                continue
            rows.append(
                {
                    "case": case.case_name,
                    "scenario": case.scenario_name,
                    "planner": case.planner_name,
                    "variant": variant,
                    "include_in_aggregate": case.include_in_aggregate,
                    "plan_status": audit.plan_status,
                    "plan_success": audit.plan_success,
                    "plan_reason": audit.plan_reason or "",
                    "repair_accepted": case.repair_accepted,
                    "repair_reason": case.repair_reason,
                    "sample_count": len(audit.points),
                    "valid_points": audit.valid_points,
                    "invalid_points": audit.invalid_points,
                    "unknown_points": audit.unknown_points,
                    "coverage_ratio": audit.coverage_ratio,
                    "max_uncovered_s": audit.max_uncovered_s,
                    "prefilter_time_s": audit.prefilter_time_s,
                    "online_time_s": audit.online_time_s,
                    "full_time_s": audit.full_time_s,
                    "planning_time_s": audit.planning_time_s,
                    "repair_time_s": audit.repair_time_s,
                    "end_to_end_s": audit.end_to_end_s,
                    "full_end_to_end_s": audit.full_end_to_end_s,
                    "path_length_m": audit.path_length_m,
                    "duration_s": audit.duration_s,
                    "min_clearance_m": audit.min_clearance_m,
                    "coverage_intervals": ";".join(
                        f"{lo:g}-{hi:g}" for lo, hi in audit.coverage_intervals
                    ),
                    "uncovered_intervals": ";".join(
                        f"{lo:g}-{hi:g}" for lo, hi in audit.uncovered_intervals
                    ),
                    "failure_sources": ";".join(
                        f"{name}:{count}" for name, count in audit.failure_sources
                    ),
                }
            )
    _write_csv(path, rows)


def _write_points_csv(path: Path, cases: Sequence[M71CaseResult]) -> None:
    rows: list[dict[str, Any]] = []
    for case in cases:
        repair_variant = "repair_accepted" if case.repair_accepted else "repair_attempt"
        for audit, variant in ((case.baseline, "baseline"), (case.repair, repair_variant)):
            if audit is None:
                continue
            for point in audit.points:
                rows.append(
                    {
                        "case": case.case_name,
                        "planner": case.planner_name,
                        "variant": variant,
                        "index": point.index,
                        "t_s": point.t_s,
                        "x_m": point.position_ned_m[0],
                        "y_m": point.position_ned_m[1],
                        "z_m": point.position_ned_m[2],
                        "clearance_m": point.clearance_m,
                        "prefilter_reason": point.prefilter_reason or "",
                        "online_status": point.online_status,
                        "online_reason": point.online_reason or "",
                        "online_elapsed_s": point.online_elapsed_s,
                        "online_early_stopped": point.online_early_stopped,
                        "online_evaluated_checks": point.online_evaluated_checks,
                        "full_status": point.full_status,
                        "full_reason": point.full_reason or "",
                        "full_elapsed_s": point.full_elapsed_s,
                        "full_early_stopped": point.full_early_stopped,
                        "full_evaluated_checks": point.full_evaluated_checks,
                        "certificate_valid_from_s": (
                            ""
                            if point.certificate_valid_from_s is None
                            else point.certificate_valid_from_s
                        ),
                        "certificate_valid_until_s": (
                            ""
                            if point.certificate_valid_until_s is None
                            else point.certificate_valid_until_s
                        ),
                        "failure_source": point.failure_source or "",
                    }
                )
    _write_csv(path, rows)


def _write_trajectories_csv(path: Path, cases: Sequence[M71CaseResult]) -> None:
    rows: list[dict[str, Any]] = []
    for case in cases:
        repair_variant = "repair_accepted" if case.repair_accepted else "repair_attempt"
        for audit, variant in ((case.baseline, "baseline"), (case.repair, repair_variant)):
            if audit is None or audit.trajectory is None:
                continue
            trajectory = audit.trajectory
            for index in range(trajectory.t_s.shape[0]):
                rows.append(
                    {
                        "case": case.case_name,
                        "planner": case.planner_name,
                        "variant": variant,
                        "index": index,
                        "t_s": trajectory.t_s[index],
                        "x_m": trajectory.position_ned_m[index, 0],
                        "y_m": trajectory.position_ned_m[index, 1],
                        "z_m": trajectory.position_ned_m[index, 2],
                        "qx": trajectory.quat_xyzw[index, 0],
                        "qy": trajectory.quat_xyzw[index, 1],
                        "qz": trajectory.quat_xyzw[index, 2],
                        "qw": trajectory.quat_xyzw[index, 3],
                        "vx_body_mps": trajectory.linear_velocity_body_mps[index, 0],
                        "vy_body_mps": trajectory.linear_velocity_body_mps[index, 1],
                        "vz_body_mps": trajectory.linear_velocity_body_mps[index, 2],
                    }
                )
    _write_csv(path, rows)


def _write_repair_attempts_csv(path: Path, cases: Sequence[M71CaseResult]) -> None:
    rows: list[dict[str, Any]] = []
    for case in cases:
        for attempt in case.repair_attempts:
            rows.append(
                {
                    "case": case.case_name,
                    "planner": case.planner_name,
                    "candidate_index": attempt.candidate_index,
                    "source": attempt.source,
                    "via_x_m": "" if attempt.via_ned_m is None else attempt.via_ned_m[0],
                    "via_y_m": "" if attempt.via_ned_m is None else attempt.via_ned_m[1],
                    "via_z_m": "" if attempt.via_ned_m is None else attempt.via_ned_m[2],
                    "candidate_status": attempt.candidate_status or "",
                    "geometric_safe": attempt.geometric_safe,
                    "plan_success": attempt.plan_success,
                    "coverage_ratio": attempt.coverage_ratio,
                    "max_uncovered_s": attempt.max_uncovered_s,
                    "accepted": attempt.accepted,
                    "reason": attempt.reason,
                }
            )
    _write_csv(path, rows)


def _write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    write_csv_allow_empty(path, rows)


def _timing(values: Sequence[float]) -> dict[str, float | int]:
    if not values:
        return {"count": 0, "median": 0.0, "mean": 0.0, "max": 0.0}
    array = np.asarray(values, dtype=np.float64)
    return {
        "count": int(array.size),
        "median": float(np.median(array)),
        "mean": float(np.mean(array)),
        "max": float(np.max(array)),
    }


def _audit_group(audits: Sequence[PathAudit]) -> dict[str, Any]:
    full_end_to_end = _timing([audit.full_end_to_end_s for audit in audits])
    full_median = float(full_end_to_end["median"])
    share = {
        name: 0.0
        if full_median <= 0.0
        else float(_timing([value(audit) for audit in audits])["median"]) / full_median
        for name, value in (
            ("planning", lambda audit: audit.planning_time_s),
            ("prefilter", lambda audit: audit.prefilter_time_s),
            ("online", lambda audit: audit.online_time_s),
            ("full", lambda audit: audit.full_time_s),
        )
    }
    return {
        "paths": len(audits),
        "plan_success": sum(audit.plan_success for audit in audits),
        "plan_success_rate": 0.0
        if not audits
        else sum(audit.plan_success for audit in audits) / len(audits),
        "sampled_points": sum(len(audit.points) for audit in audits),
        "valid_points": sum(audit.valid_points for audit in audits),
        "invalid_points": sum(audit.invalid_points for audit in audits),
        "unknown_points": sum(audit.unknown_points for audit in audits),
        "coverage_ratio": _timing([audit.coverage_ratio for audit in audits]),
        "max_uncovered_s": _timing([audit.max_uncovered_s for audit in audits]),
        "prefilter_time_s": _timing([audit.prefilter_time_s for audit in audits]),
        "online_time_s": _timing([audit.online_time_s for audit in audits]),
        "full_time_s": _timing([audit.full_time_s for audit in audits]),
        "planning_time_s": _timing([audit.planning_time_s for audit in audits]),
        "end_to_end_s": _timing([audit.end_to_end_s for audit in audits]),
        "full_end_to_end_s": full_end_to_end,
        "time_share_of_full_end_to_end": share,
    }


def _summary_payload(result: M71ExperimentResult) -> dict[str, Any]:
    aggregate_cases = tuple(case for case in result.cases if case.include_in_aggregate)
    baseline = tuple(case.baseline for case in aggregate_cases)
    repair_attempted = tuple(case.repair for case in aggregate_cases if case.repair is not None)
    repair_accepted = tuple(
        case.repair for case in aggregate_cases if case.repair is not None and case.repair_accepted
    )
    failure_counts: Counter[str] = Counter()
    for case in result.cases:
        for audit in (case.baseline, case.repair):
            if audit is None:
                continue
            failure_counts.update(dict(audit.failure_sources))
    by_planner: dict[str, Any] = {}
    for planner_name in result.config.planner_names:
        planner_cases = tuple(case for case in aggregate_cases if case.planner_name == planner_name)
        by_planner[planner_name] = {
            "baseline": _audit_group(tuple(case.baseline for case in planner_cases)),
            "repair_attempted": _audit_group(
                tuple(case.repair for case in planner_cases if case.repair is not None)
            ),
            "repair_accepted": _audit_group(
                tuple(
                    case.repair
                    for case in planner_cases
                    if case.repair is not None and case.repair_accepted
                )
            ),
            "repair_accepted_count": sum(case.repair_accepted for case in planner_cases),
        }
    return {
        "schema_version": 1,
        "status": "M7.1 complete; real A*/RRT* paths audited, cost probe excluded",
        "elapsed_s": result.elapsed_s,
        "config": {
            **asdict(result.config),
            "profile_digest": result.config.profile.digest,
        },
        "case_count": len(result.cases),
        "path_count": len(result.cases),
        "aggregate_case_count": len(aggregate_cases),
        "excluded_cases": sorted(
            case.case_name for case in result.cases if not case.include_in_aggregate
        ),
        "baseline": _audit_group(baseline),
        "repair_attempted": _audit_group(repair_attempted),
        "repair_accepted": _audit_group(repair_accepted),
        "repair_accepted_count": sum(case.repair_accepted for case in aggregate_cases),
        "repair_improved_count": sum(
            case.repair is not None
            and case.repair.coverage_ratio > case.baseline.coverage_ratio + 1e-12
            for case in aggregate_cases
        ),
        "by_planner": by_planner,
        "failure_sources": dict(sorted(failure_counts.items())),
        "cases": [
            {
                "case": case.case_name,
                "planner": case.planner_name,
                "include_in_aggregate": case.include_in_aggregate,
                "baseline_coverage_ratio": case.baseline.coverage_ratio,
                "baseline_max_uncovered_s": case.baseline.max_uncovered_s,
                "repair_coverage_ratio": None
                if case.repair is None
                else case.repair.coverage_ratio,
                "repair_max_uncovered_s": None
                if case.repair is None
                else case.repair.max_uncovered_s,
                "repair_accepted": case.repair_accepted,
                "repair_reason": case.repair_reason,
                "repair_attempts": len(case.repair_attempts),
            }
            for case in result.cases
        ],
    }


def _write_summary(path: Path, result: M71ExperimentResult) -> None:
    path.write_text(
        json.dumps(_summary_payload(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_manifest(path: Path, result: M71ExperimentResult) -> None:
    payload = {
        "schema_version": 1,
        "experiment": "M7.1 real planner trajectory certificate audit",
        "hardware": hardware_manifest(),
        "config": {
            **asdict(result.config),
            "profile": result.config.profile.manifest(),
        },
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
