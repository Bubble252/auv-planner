"""Lazy public exports for the underwater global planner package."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

_CORE_EXPORTS = {
    "BODY_FRAME",
    "WORLD_FRAME",
    "ActuatorCommand",
    "AlosSolution",
    "CapabilitySet",
    "ClearanceDetails",
    "ControlProposal",
    "CurrentField",
    "DepthShearCurrent",
    "EvalResult",
    "Guidance",
    "HullSpec",
    "LocalObservation",
    "Obstacle",
    "ObstacleMap",
    "OccupancyGrid",
    "PlanReason",
    "PlanRequest",
    "PlanResult",
    "PlanStatus",
    "RecoveryCertificate",
    "Reference",
    "Remus100ActuatorCommand",
    "Remus100ControlDiagnostics",
    "Remus100TrackingController",
    "SafeCommand",
    "SafetyContext",
    "SafetyFilter",
    "ScenarioConfig",
    "SimulationSnapshot",
    "SimulatorBackend",
    "State",
    "SweepResult",
    "TaskSpec",
    "ThreeDAlosGuidance",
    "TrackingController",
    "Trajectory",
    "UniformCurrent",
    "VehicleSpec",
    "WorldSnapshot",
    "hull_clearance",
    "hull_clearance_details",
    "hull_from_vehicle",
    "hull_sphere_centers",
    "obstacle_signed_distance",
    "point_clearance",
    "point_clearance_details",
    "trajectory_sweep",
}

_EXPORTS = {name: "auv_core" for name in _CORE_EXPORTS}
_EXPORTS.update(
    {
        "GlobalPlanner": ".interfaces",
        "LocalPlanner": ".interfaces",
        "MssRemus100Backend": ".dynamics",
        "PathMetrics": ".metrics",
        "PvsRemus100Backend": ".dynamics",
        "compute_path_metrics": ".metrics",
    }
)

__all__ = sorted(_EXPORTS)


def __getattr__(name: str) -> object:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(__all__)


if TYPE_CHECKING:
    from auv_core import (
        BODY_FRAME,
        WORLD_FRAME,
        ActuatorCommand,
        AlosSolution,
        CapabilitySet,
        ClearanceDetails,
        ControlProposal,
        CurrentField,
        DepthShearCurrent,
        EvalResult,
        Guidance,
        HullSpec,
        LocalObservation,
        Obstacle,
        ObstacleMap,
        OccupancyGrid,
        PlanReason,
        PlanRequest,
        PlanResult,
        PlanStatus,
        RecoveryCertificate,
        Reference,
        Remus100ActuatorCommand,
        Remus100ControlDiagnostics,
        Remus100TrackingController,
        SafeCommand,
        SafetyContext,
        SafetyFilter,
        ScenarioConfig,
        SimulationSnapshot,
        SimulatorBackend,
        State,
        SweepResult,
        TaskSpec,
        ThreeDAlosGuidance,
        TrackingController,
        Trajectory,
        UniformCurrent,
        VehicleSpec,
        WorldSnapshot,
        hull_clearance,
        hull_clearance_details,
        hull_from_vehicle,
        hull_sphere_centers,
        obstacle_signed_distance,
        point_clearance,
        point_clearance_details,
        trajectory_sweep,
    )

    from .dynamics import MssRemus100Backend, PvsRemus100Backend
    from .interfaces import GlobalPlanner, LocalPlanner
    from .metrics import PathMetrics, compute_path_metrics
