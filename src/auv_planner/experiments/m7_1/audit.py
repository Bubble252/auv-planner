"""Trajectory sampling, certificate coverage, and M7.1 path auditing."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from time import perf_counter

import numpy as np
from auv_core.contracts import FloatArray, PlanResult, ScenarioConfig, State, Trajectory

from ...metrics import compute_path_metrics
from ...recovery import (
    RecoveryConfig,
    RecoveryQueryMode,
    RecoveryQueryPolicy,
    RecoveryQueryResult,
    RecoveryQuerySession,
    RecoveryQueryStatus,
    prefilter_state,
)
from .types import AuditPoint, M71Config, PathAudit


def sample_trajectory_states(trajectory: Trajectory, interval_s: float) -> tuple[State, ...]:
    if not np.isfinite(interval_s) or interval_s <= 0.0:
        raise ValueError("interval_s must be finite and positive")
    times = trajectory.t_s
    targets = [
        float(value)
        for value in np.arange(float(times[0]), float(times[-1]), interval_s, dtype=np.float64)
    ]
    if not targets or float(targets[-1]) < float(times[-1]) - 1e-12:
        targets.append(float(times[-1]))
    elif abs(float(targets[-1]) - float(times[-1])) <= 1e-12:
        targets[-1] = float(times[-1])
    states: list[State] = []
    for target in targets:
        index = int(np.searchsorted(times, target, side="right") - 1)
        index = int(np.clip(index, 0, times.shape[0] - 1))
        if index >= times.shape[0] - 1 or abs(float(times[index]) - float(target)) <= 1e-12:
            if abs(float(times[index]) - float(target)) <= 1e-12:
                position = trajectory.position_ned_m[index]
                quat = trajectory.quat_xyzw[index]
                velocity = trajectory.linear_velocity_body_mps[index]
                angular = trajectory.angular_velocity_body_rps[index]
            else:
                position = trajectory.position_ned_m[-1]
                quat = trajectory.quat_xyzw[-1]
                velocity = trajectory.linear_velocity_body_mps[-1]
                angular = trajectory.angular_velocity_body_rps[-1]
        else:
            next_index = index + 1
            duration = float(times[next_index] - times[index])
            fraction = 0.0 if duration <= 1e-12 else float((target - times[index]) / duration)
            position = (1.0 - fraction) * trajectory.position_ned_m[
                index
            ] + fraction * trajectory.position_ned_m[next_index]
            quat = _slerp(
                trajectory.quat_xyzw[index],
                trajectory.quat_xyzw[next_index],
                fraction,
            )
            velocity = (1.0 - fraction) * trajectory.linear_velocity_body_mps[
                index
            ] + fraction * trajectory.linear_velocity_body_mps[next_index]
            angular = (1.0 - fraction) * trajectory.angular_velocity_body_rps[
                index
            ] + fraction * trajectory.angular_velocity_body_rps[next_index]
        states.append(
            State(
                t_s=float(target),
                position_ned_m=np.asarray(position, dtype=np.float64).copy(),
                quat_xyzw=np.asarray(quat, dtype=np.float64).copy(),
                linear_velocity_body_mps=np.asarray(velocity, dtype=np.float64).copy(),
                angular_velocity_body_rps=np.asarray(angular, dtype=np.float64).copy(),
                frame_id=trajectory.frame_id,
            )
        )
    return tuple(states)


def _slerp(quat_a: FloatArray, quat_b: FloatArray, fraction: float) -> FloatArray:
    first = np.asarray(quat_a, dtype=np.float64)
    second = np.asarray(quat_b, dtype=np.float64)
    first = first / np.linalg.norm(first)
    second = second / np.linalg.norm(second)
    dot = float(np.dot(first, second))
    if dot < 0.0:
        second = -second
        dot = -dot
    dot = float(np.clip(dot, -1.0, 1.0))
    if dot > 0.9995:
        result = first + fraction * (second - first)
        return result / np.linalg.norm(result)
    theta = float(np.arccos(dot))
    sin_theta = float(np.sin(theta))
    if sin_theta <= 1e-12:
        return first.copy()
    first_weight = float(np.sin((1.0 - fraction) * theta) / sin_theta)
    second_weight = float(np.sin(fraction * theta) / sin_theta)
    return first_weight * first + second_weight * second


def _merge_intervals(
    intervals: Iterable[tuple[float, float]],
    *,
    start: float,
    end: float,
) -> tuple[tuple[float, float], ...]:
    clipped = sorted(
        (max(start, float(lo)), min(end, float(hi)))
        for lo, hi in intervals
        if float(hi) > start and float(lo) < end
    )
    if not clipped:
        return ()
    merged: list[tuple[float, float]] = [clipped[0]]
    for lo, hi in clipped[1:]:
        previous_lo, previous_hi = merged[-1]
        if lo <= previous_hi + 1e-12:
            merged[-1] = (previous_lo, max(previous_hi, hi))
        else:
            merged.append((lo, hi))
    return tuple(merged)


def coverage_metrics(
    points: Sequence[AuditPoint],
    *,
    start_s: float,
    end_s: float,
) -> tuple[float, float, tuple[tuple[float, float], ...], tuple[tuple[float, float], ...]]:
    if end_s < start_s:
        raise ValueError("end_s must not precede start_s")
    intervals = _merge_intervals(
        (
            (point.certificate_valid_from_s, point.certificate_valid_until_s)
            for point in points
            if point.full_status == RecoveryQueryStatus.VALID.value
            and point.certificate_valid_from_s is not None
            and point.certificate_valid_until_s is not None
        ),
        start=start_s,
        end=end_s,
    )
    duration = end_s - start_s
    covered = sum(hi - lo for lo, hi in intervals)
    uncovered: list[tuple[float, float]] = []
    cursor = start_s
    for lo, hi in intervals:
        if lo > cursor + 1e-12:
            uncovered.append((cursor, lo))
        cursor = max(cursor, hi)
    if cursor < end_s - 1e-12:
        uncovered.append((cursor, end_s))
    ratio = 0.0 if duration <= 1e-12 else min(1.0, covered / duration)
    max_uncovered = max((hi - lo for lo, hi in uncovered), default=0.0)
    return ratio, max_uncovered, intervals, tuple(uncovered)


def _failure_source(
    *,
    prefilter_reason: str | None,
    full_result: RecoveryQueryResult | None,
) -> str | None:
    if full_result is not None and full_result.status is RecoveryQueryStatus.VALID:
        return None
    prefix = prefilter_reason or ""
    if "collision" in prefix:
        return "initial_obstacle_collision"
    if "out_of_bounds" in prefix:
        return "initial_out_of_bounds"
    if "clearance_below_required" in prefix:
        return "initial_clearance"
    if full_result is None:
        return "certificate_unavailable"
    reason = str(full_result.reason or "")
    if "diagnosis_coast_unsafe" in reason:
        return "diagnosis_coast"
    assessment = full_result.assessment
    if assessment is not None:
        maneuver_reasons = [
            str(check.failure_reason or "")
            for fault_check in assessment.fault_checks
            for check in fault_check.checks
        ]
        fault_reasons = [str(check.failure_reason or "") for check in assessment.fault_checks]
        if any("no_available_backup_maneuver" in text for text in fault_reasons):
            return "backup_unavailable"
        if any("no_backup_maneuver_generated" in text for text in fault_reasons):
            return "backup_unavailable"
        if any("out_of_bounds" in text for text in maneuver_reasons):
            return "backup_out_of_bounds"
        if any("collision" in text for text in maneuver_reasons):
            return "backup_collision"
        if any("clearance_below_required" in text for text in maneuver_reasons):
            return "backup_clearance"
        if any("actuator_limit" in text for text in maneuver_reasons):
            return "actuator_limit"
        if any(not check.checks for check in assessment.fault_checks):
            return "backup_unavailable"
    if "no_available_backup" in reason or "no_backup_maneuver_generated" in reason:
        return "backup_unavailable"
    if "no_safe_backup" in reason:
        return "certificate_model_conservative"
    return "certificate_unclassified"


def audit_trajectory(
    trajectory: Trajectory,
    scenario: ScenarioConfig,
    *,
    case_name: str,
    planner_name: str,
    variant: str,
    include_in_aggregate: bool,
    plan_status: str,
    plan_success: bool,
    plan_reason: str | None,
    planning_time_s: float,
    repair_time_s: float,
    config: M71Config,
    safe_anchor_ned_m: FloatArray | None = None,
) -> PathAudit:
    states = sample_trajectory_states(trajectory, config.audit_interval_s)
    profile = config.profile
    recovery_config = RecoveryConfig()

    prefilters = []
    prefilter_time = 0.0
    for state in states:
        started = perf_counter()
        prefilter = prefilter_state(state, scenario.world, scenario.vehicle, recovery_config)
        prefilter_time += perf_counter() - started
        prefilters.append(prefilter)

    online_session = RecoveryQuerySession(
        policy=RecoveryQueryPolicy(
            budget_s=config.online_budget_s,
            use_cache=True,
            use_prefilter=False,
            mode=RecoveryQueryMode.ONLINE_FAST,
            parallel_workers=1,
        )
    )
    online_results: list[RecoveryQueryResult | None] = []
    online_time = 0.0
    for state, prefilter in zip(states, prefilters, strict=True):
        if prefilter.rejected:
            online_results.append(None)
            continue
        result = online_session.query(
            state,
            scenario.world,
            scenario.vehicle,
            config=recovery_config,
            profile=profile,
            safe_anchor_ned_m=safe_anchor_ned_m,
        )
        online_results.append(result)
        online_time += result.elapsed_s

    full_session = RecoveryQuerySession(
        policy=RecoveryQueryPolicy(
            budget_s=None,
            use_cache=True,
            use_prefilter=False,
            mode=RecoveryQueryMode.FULL,
            parallel_workers=config.full_workers,
        )
    )
    full_results: list[RecoveryQueryResult | None] = []
    full_time = 0.0
    for state, prefilter in zip(states, prefilters, strict=True):
        if prefilter.rejected:
            full_results.append(None)
            continue
        result = full_session.query(
            state,
            scenario.world,
            scenario.vehicle,
            config=recovery_config,
            profile=profile,
            safe_anchor_ned_m=safe_anchor_ned_m,
        )
        full_results.append(result)
        full_time += result.elapsed_s

    points: list[AuditPoint] = []
    online_reason: str | None
    full_reason: str | None
    valid_from: float | None
    valid_until: float | None
    for index, (state, prefilter, online, full) in enumerate(
        zip(states, prefilters, online_results, full_results, strict=True)
    ):
        if prefilter.rejected:
            prefilter_reason: str | None = f"prefilter:{prefilter.reason}"
            online_status = RecoveryQueryStatus.INVALID.value
            full_status = RecoveryQueryStatus.INVALID.value
            online_reason = prefilter_reason
            full_reason = prefilter_reason
            online_elapsed = 0.0
            full_elapsed = 0.0
            online_early = False
            full_early = False
            online_checks = 0
            full_checks = 0
            valid_from = None
            valid_until = None
        else:
            assert online is not None
            online_status = online.status.value
            online_reason = online.reason
            online_elapsed = online.elapsed_s
            online_early = online.early_stopped
            online_checks = online.evaluated_checks
            if full is None:
                full_status = RecoveryQueryStatus.INVALID.value
                full_reason = "missing_full_result"
                full_elapsed = 0.0
                full_early = False
                full_checks = 0
                valid_from = None
                valid_until = None
            else:
                full_status = full.status.value
                full_reason = full.reason
                full_elapsed = full.elapsed_s
                full_early = full.early_stopped
                full_checks = full.evaluated_checks
                certificate = None if full.assessment is None else full.assessment.certificate
                valid_from = None if certificate is None else certificate.valid_from_s
                valid_until = None if certificate is None else certificate.valid_until_s
        points.append(
            AuditPoint(
                index=index,
                t_s=float(state.t_s),
                position_ned_m=state.position_ned_m.copy(),
                quat_xyzw=state.quat_xyzw.copy(),
                clearance_m=float(prefilter.current_clearance_m),
                prefilter_reason=None
                if not prefilter.rejected
                else f"prefilter:{prefilter.reason}",
                online_status=online_status,
                online_reason=online_reason,
                online_elapsed_s=float(online_elapsed),
                online_early_stopped=online_early,
                online_evaluated_checks=online_checks,
                full_status=full_status,
                full_reason=full_reason,
                full_elapsed_s=float(full_elapsed),
                full_early_stopped=full_early,
                full_evaluated_checks=full_checks,
                certificate_valid_from_s=valid_from,
                certificate_valid_until_s=valid_until,
                failure_source=_failure_source(
                    prefilter_reason=None
                    if not prefilter.rejected
                    else f"prefilter:{prefilter.reason}",
                    full_result=full,
                ),
            )
        )

    start_s = float(points[0].t_s)
    end_s = float(points[-1].t_s)
    coverage_ratio, max_uncovered, coverage_intervals, uncovered_intervals = coverage_metrics(
        points,
        start_s=start_s,
        end_s=end_s,
    )
    metrics = compute_path_metrics(trajectory, scenario.world.obstacle_map, scenario.vehicle)
    failures = Counter(point.failure_source for point in points if point.failure_source is not None)
    return PathAudit(
        case_name=case_name,
        scenario_name=scenario.name,
        planner_name=planner_name,
        variant=variant,
        include_in_aggregate=include_in_aggregate,
        plan_status=plan_status,
        plan_success=plan_success,
        plan_reason=plan_reason,
        planning_time_s=float(planning_time_s),
        repair_time_s=float(repair_time_s),
        trajectory=trajectory,
        points=tuple(points),
        prefilter_time_s=float(prefilter_time),
        online_time_s=float(online_time),
        full_time_s=float(full_time),
        path_length_m=float(metrics.path_length_m),
        duration_s=float(metrics.duration_s),
        min_clearance_m=float(metrics.min_clearance_m),
        coverage_ratio=float(coverage_ratio),
        max_uncovered_s=float(max_uncovered),
        coverage_intervals=coverage_intervals,
        uncovered_intervals=uncovered_intervals,
        failure_sources=tuple(sorted(failures.items())),
    )


def _failed_path_audit(
    *,
    case_name: str,
    scenario: ScenarioConfig,
    planner_name: str,
    include_in_aggregate: bool,
    plan: PlanResult,
    config: M71Config,
) -> PathAudit:
    duration = float(scenario.constraints.get("planning_timeout_s", config.astar_timeout_s))
    return PathAudit(
        case_name=case_name,
        scenario_name=scenario.name,
        planner_name=planner_name,
        variant="baseline",
        include_in_aggregate=include_in_aggregate,
        plan_status=plan.status.value,
        plan_success=False,
        plan_reason=plan.reason,
        planning_time_s=float(plan.planning_time_s),
        repair_time_s=0.0,
        trajectory=None,
        points=(),
        prefilter_time_s=0.0,
        online_time_s=0.0,
        full_time_s=0.0,
        path_length_m=0.0,
        duration_s=duration,
        min_clearance_m=0.0,
        coverage_ratio=0.0,
        max_uncovered_s=duration,
        coverage_intervals=(),
        uncovered_intervals=((0.0, duration),) if duration > 0.0 else (),
        failure_sources=(("planner_failed", 1),),
    )
