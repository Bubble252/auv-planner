from __future__ import annotations

from collections.abc import Iterable
from time import perf_counter

import numpy as np
from auv_core.attitude import forward_quaternion
from auv_core.contracts import (
    CapabilitySet,
    FloatArray,
    PlanReason,
    PlanRequest,
    PlanResult,
    PlanStatus,
    ScenarioConfig,
    State,
    TaskSpec,
    Trajectory,
)
from auv_core.geometry import trajectory_sweep

from ...evaluation.runner import evaluate_plan
from ...planners.common import SegmentValidator, build_trajectory
from ...recovery import (
    RecoveryConfig,
    RecoveryQueryMode,
    RecoveryQueryPolicy,
    RecoveryQuerySession,
    RecoveryQueryStatus,
    prefilter_state,
)
from .audit import audit_trajectory
from .types import AuditPoint, M71CaseSpec, M71Config, PathAudit, RepairAttempt


def _plan_request(
    scenario: ScenarioConfig,
    *,
    request_id: str,
    seed: int,
    start: State | None = None,
    goal_ned_m: FloatArray | None = None,
    goal_radius_m: float | None = None,
    timeout_s: float | None = None,
) -> PlanRequest:
    constraints = dict(scenario.constraints)
    if timeout_s is not None:
        constraints["planning_timeout_s"] = timeout_s
    return PlanRequest(
        request_id=request_id,
        start=scenario.start if start is None else start,
        task=TaskSpec(
            goal_ned_m=scenario.goal_ned_m if goal_ned_m is None else goal_ned_m,
            goal_radius_m=scenario.goal_radius_m if goal_radius_m is None else goal_radius_m,
            constraints=constraints,
        ),
        world=scenario.world,
        vehicle=scenario.vehicle,
        capability=CapabilitySet(
            available_actuators=("propeller", "yaw_fin", "pitch_fin"),
            effectiveness={"propeller": 1.0, "yaw_fin": 1.0, "pitch_fin": 1.0},
        ),
        seed=seed,
        reason=PlanReason.INITIAL,
    )


def _prefix_positions(
    trajectory: Trajectory, end_s: float, end_position: FloatArray
) -> list[FloatArray]:
    positions = [
        trajectory.position_ned_m[index].copy()
        for index in range(trajectory.t_s.shape[0])
        if float(trajectory.t_s[index]) < end_s - 1e-12
    ]
    if not positions or float(np.linalg.norm(positions[-1] - end_position)) > 1e-12:
        positions.append(end_position.copy())
    return positions


def _suffix_positions(
    trajectory: Trajectory, start_s: float, start_position: FloatArray
) -> list[FloatArray]:
    positions = [start_position.copy()]
    positions.extend(
        trajectory.position_ned_m[index].copy()
        for index in range(trajectory.t_s.shape[0])
        if float(trajectory.t_s[index]) > start_s + 1e-12
    )
    return positions


def _dedupe_positions(positions: Iterable[FloatArray]) -> FloatArray:
    cleaned: list[FloatArray] = []
    for position in positions:
        candidate = np.asarray(position, dtype=np.float64)
        if not cleaned or float(np.linalg.norm(candidate - cleaned[-1])) > 1e-12:
            cleaned.append(candidate.copy())
    if len(cleaned) < 2:
        cleaned.append(cleaned[0].copy())
    return np.vstack(cleaned)


def _candidate_states(
    scenario: ScenarioConfig,
    baseline: PathAudit,
    spec: M71CaseSpec,
    config: M71Config,
) -> tuple[tuple[State, str], ...]:
    if config.max_repair_candidates <= 0 or not baseline.points:
        return ()
    invalid_index = _first_invalid_index(baseline)
    if invalid_index <= 0 or invalid_index >= len(baseline.points) - 1:
        return ()
    prev_index = max(
        (
            index
            for index in range(invalid_index)
            if baseline.points[index].full_status == RecoveryQueryStatus.VALID.value
        ),
        default=0,
    )
    next_index = min(
        (
            index
            for index in range(invalid_index + 1, len(baseline.points))
            if baseline.points[index].full_status == RecoveryQueryStatus.VALID.value
        ),
        default=len(baseline.points) - 1,
    )
    prev = baseline.points[prev_index]
    invalid = baseline.points[invalid_index]
    next_point = baseline.points[next_index]
    path_direction = next_point.position_ned_m - prev.position_ned_m
    horizontal = np.array([-path_direction[1], path_direction[0], 0.0], dtype=np.float64)
    norm = float(np.linalg.norm(horizontal))
    if norm <= 1e-12:
        horizontal = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    else:
        horizontal /= norm
    directions = (horizontal, -horizontal, np.array([0.0, 0.0, -1.0]), np.array([0.0, 0.0, 1.0]))
    candidates: list[tuple[State, str]] = []
    bounds = scenario.world.obstacle_map.bounds_ned_m
    seen: set[tuple[float, float, float]] = set()
    if spec.safe_anchor_ned_m is not None:
        point = np.asarray(spec.safe_anchor_ned_m, dtype=np.float64)
        if np.all(point >= bounds[:, 0]) and np.all(point <= bounds[:, 1]):
            key = (float(point[0]), float(point[1]), float(point[2]))
            seen.add(key)
            candidates.append(
                (
                    _candidate_state(invalid, point, next_point.position_ned_m, scenario),
                    "safe_anchor",
                )
            )
            if len(candidates) >= config.max_repair_candidates:
                return tuple(candidates)
    for radius in config.repair_offsets_m:
        for direction in directions:
            point = invalid.position_ned_m + radius * direction
            if np.any(point < bounds[:, 0]) or np.any(point > bounds[:, 1]):
                continue
            key = (float(point[0]), float(point[1]), float(point[2]))
            if key in seen:
                continue
            seen.add(key)
            candidate = _candidate_state(invalid, point, next_point.position_ned_m, scenario)
            candidates.append(
                (
                    candidate,
                    f"offset_{radius:g}m",
                )
            )
            if len(candidates) >= config.max_repair_candidates:
                return tuple(candidates)
    return tuple(candidates)


def _state_at_point(source: AuditPoint, position: FloatArray, scenario: ScenarioConfig) -> State:
    return State(
        t_s=source.t_s,
        position_ned_m=np.asarray(position, dtype=np.float64),
        quat_xyzw=source.quat_xyzw.copy(),
        linear_velocity_body_mps=np.array([scenario.vehicle.min_speed_mps, 0.0, 0.0]),
        angular_velocity_body_rps=np.zeros(3),
    )


def _candidate_state(
    invalid: AuditPoint,
    position: FloatArray,
    next_position: FloatArray,
    scenario: ScenarioConfig,
) -> State:
    direction = np.asarray(next_position, dtype=np.float64) - np.asarray(position, dtype=np.float64)
    if float(np.linalg.norm(direction)) <= 1e-12:
        direction = np.asarray(next_position, dtype=np.float64) - invalid.position_ned_m
    return State(
        t_s=invalid.t_s,
        position_ned_m=np.asarray(position, dtype=np.float64),
        quat_xyzw=forward_quaternion(direction),
        linear_velocity_body_mps=np.array([scenario.vehicle.min_speed_mps, 0.0, 0.0]),
        angular_velocity_body_rps=np.zeros(3),
    )


def _candidate_path_safe(
    previous: State,
    candidate: State,
    following: State,
    scenario: ScenarioConfig,
) -> bool:
    validator = SegmentValidator(scenario.world.obstacle_map, scenario.vehicle, max_step_m=0.1)
    if not validator.state_is_safe(candidate.position_ned_m, candidate.quat_xyzw):
        return False
    return bool(
        validator(previous.position_ned_m, candidate.position_ned_m)
        and validator(candidate.position_ned_m, following.position_ned_m)
    )


def _attempt_repair(
    baseline: PathAudit,
    scenario: ScenarioConfig,
    spec: M71CaseSpec,
    config: M71Config,
) -> tuple[PathAudit | None, tuple[RepairAttempt, ...], float, bool, str]:
    if baseline.trajectory is None:
        return None, (), 0.0, False, "baseline_plan_failed"
    if all(point.full_status == RecoveryQueryStatus.VALID.value for point in baseline.points):
        return None, (), 0.0, False, "no_invalid_points"
    invalid_index = _first_invalid_index(baseline)
    if invalid_index <= 0:
        return None, (), 0.0, False, "invalid_start_state"
    if invalid_index >= len(baseline.points) - 1:
        return None, (), 0.0, False, "invalid_goal_state"
    candidates = _candidate_states(scenario, baseline, spec, config)
    if not candidates:
        return None, (), 0.0, False, "no_repair_candidates"
    profile = config.profile
    recovery_config = RecoveryConfig()
    attempts: list[RepairAttempt] = []
    best: PathAudit | None = None
    best_ratio = baseline.coverage_ratio
    best_uncovered = baseline.max_uncovered_s
    repair_time = 0.0
    request = _plan_request(
        scenario,
        request_id=f"{spec.name}:repair",
        seed=config.seed,
    )
    prev_index = max(
        (
            index
            for index in range(invalid_index)
            if baseline.points[index].full_status == RecoveryQueryStatus.VALID.value
        ),
        default=0,
    )
    next_index = min(
        (
            index
            for index in range(invalid_index + 1, len(baseline.points))
            if baseline.points[index].full_status == RecoveryQueryStatus.VALID.value
        ),
        default=len(baseline.points) - 1,
    )
    prev_point = baseline.points[prev_index]
    next_point = baseline.points[next_index]
    previous = _state_at_point(prev_point, prev_point.position_ned_m, scenario)
    following = _state_at_point(next_point, next_point.position_ned_m, scenario)
    for candidate_index, (candidate, source) in enumerate(candidates):
        started = perf_counter()
        prefilter = prefilter_state(candidate, scenario.world, scenario.vehicle, recovery_config)
        if prefilter.rejected:
            repair_time += perf_counter() - started
            attempts.append(
                RepairAttempt(
                    candidate_index=candidate_index,
                    source=source,
                    via_ned_m=candidate.position_ned_m.copy(),
                    candidate_status=RecoveryQueryStatus.INVALID.value,
                    geometric_safe=False,
                    plan_success=False,
                    coverage_ratio=0.0,
                    max_uncovered_s=baseline.duration_s,
                    accepted=False,
                    reason=f"prefilter:{prefilter.reason}",
                )
            )
            continue
        candidate_session = RecoveryQuerySession(
            policy=RecoveryQueryPolicy(
                budget_s=None,
                use_cache=False,
                use_prefilter=False,
                mode=RecoveryQueryMode.ONLINE_FAST,
            )
        )
        candidate_result = candidate_session.query(
            candidate,
            scenario.world,
            scenario.vehicle,
            config=recovery_config,
            profile=profile,
            safe_anchor_ned_m=spec.safe_anchor_ned_m,
        )
        if candidate_result.status is not RecoveryQueryStatus.VALID:
            repair_time += perf_counter() - started
            attempts.append(
                RepairAttempt(
                    candidate_index=candidate_index,
                    source=source,
                    via_ned_m=candidate.position_ned_m.copy(),
                    candidate_status=candidate_result.status.value,
                    geometric_safe=False,
                    plan_success=False,
                    coverage_ratio=0.0,
                    max_uncovered_s=baseline.duration_s,
                    accepted=False,
                    reason=str(candidate_result.reason or "candidate_certificate_invalid"),
                )
            )
            continue
        if not _candidate_path_safe(previous, candidate, following, scenario):
            repair_time += perf_counter() - started
            attempts.append(
                RepairAttempt(
                    candidate_index=candidate_index,
                    source=source,
                    via_ned_m=candidate.position_ned_m.copy(),
                    candidate_status=candidate_result.status.value,
                    geometric_safe=False,
                    plan_success=False,
                    coverage_ratio=0.0,
                    max_uncovered_s=baseline.duration_s,
                    accepted=False,
                    reason="geometric_path_unsafe",
                )
            )
            continue
        waypoints = _dedupe_positions(
            _prefix_positions(baseline.trajectory, prev_point.t_s, prev_point.position_ned_m)
            + [candidate.position_ned_m]
            + _suffix_positions(baseline.trajectory, next_point.t_s, next_point.position_ned_m)
        )
        repaired_trajectory = build_trajectory(
            waypoints,
            request,
            trajectory_id=f"{spec.name}:{baseline.planner_name}:repair",
        )
        sweep = trajectory_sweep(
            repaired_trajectory,
            scenario.world.obstacle_map,
            scenario.vehicle,
            max_translation_step_m=0.05,
            max_rotation_step_rad=0.05,
        )
        if not sweep.is_safe:
            repair_time += perf_counter() - started
            attempts.append(
                RepairAttempt(
                    candidate_index=candidate_index,
                    source=source,
                    via_ned_m=candidate.position_ned_m.copy(),
                    candidate_status=candidate_result.status.value,
                    geometric_safe=False,
                    plan_success=False,
                    coverage_ratio=0.0,
                    max_uncovered_s=baseline.duration_s,
                    accepted=False,
                    reason=f"trajectory_sweep:{sweep.failure_reason}",
                )
            )
            continue
        candidate_planning_time = perf_counter() - started
        plan = PlanResult(
            status=PlanStatus.OK,
            trajectory=repaired_trajectory,
            cost=float(np.sum(np.linalg.norm(np.diff(waypoints, axis=0), axis=1))),
            certificate=None,
            planning_time_s=baseline.planning_time_s + repair_time + candidate_planning_time,
            plan_id=f"{spec.name}:{baseline.planner_name}:repair",
        )
        evaluation = evaluate_plan(request, plan)
        repaired = audit_trajectory(
            repaired_trajectory,
            scenario,
            case_name=spec.name,
            planner_name=baseline.planner_name,
            variant="repair_attempt",
            include_in_aggregate=spec.include_in_aggregate,
            plan_status=plan.status.value,
            plan_success=evaluation.success,
            plan_reason=plan.reason,
            planning_time_s=plan.planning_time_s,
            repair_time_s=repair_time + candidate_planning_time,
            config=config,
            safe_anchor_ned_m=spec.safe_anchor_ned_m,
        )
        repair_time += candidate_planning_time
        is_better = evaluation.success and (
            repaired.coverage_ratio > best_ratio + 1e-12
            or (
                abs(repaired.coverage_ratio - best_ratio) <= 1e-12
                and repaired.max_uncovered_s < best_uncovered - 1e-12
            )
        )
        if is_better:
            best = repaired
            best_ratio = repaired.coverage_ratio
            best_uncovered = repaired.max_uncovered_s
        attempts.append(
            RepairAttempt(
                candidate_index=candidate_index,
                source=source,
                via_ned_m=candidate.position_ned_m.copy(),
                candidate_status=candidate_result.status.value,
                geometric_safe=True,
                plan_success=evaluation.success,
                coverage_ratio=repaired.coverage_ratio,
                max_uncovered_s=repaired.max_uncovered_s,
                accepted=is_better,
                reason=(
                    "accepted"
                    if is_better
                    else ("plan_failed" if not evaluation.success else "no_improvement")
                ),
            )
        )
        if is_better:
            return repaired, tuple(attempts), repair_time, True, "accepted"
    if best is not None:
        return best, tuple(attempts), repair_time, False, "no_improvement"
    return None, tuple(attempts), repair_time, False, "no_viable_candidate"


def _first_invalid_index(path: PathAudit) -> int:
    for index, point in enumerate(path.points):
        if point.full_status != RecoveryQueryStatus.VALID.value:
            return index
    return len(path.points) - 1
