from __future__ import annotations

from typing import Protocol, runtime_checkable

from auv_core.contracts import (
    CapabilitySet,
    ControlProposal,
    LocalObservation,
    PlanRequest,
    PlanResult,
    Reference,
)
from auv_core.interfaces import (
    Guidance,
    SafetyFilter,
    SimulatorBackend,
    TrackingController,
)


@runtime_checkable
class GlobalPlanner(Protocol):
    def plan(self, request: PlanRequest) -> PlanResult: ...


@runtime_checkable
class LocalPlanner(Protocol):
    def act(
        self,
        observation: LocalObservation,
        reference: Reference,
        capability: CapabilitySet,
    ) -> ControlProposal: ...


__all__ = [
    "GlobalPlanner",
    "Guidance",
    "LocalPlanner",
    "SafetyFilter",
    "SimulatorBackend",
    "TrackingController",
]
