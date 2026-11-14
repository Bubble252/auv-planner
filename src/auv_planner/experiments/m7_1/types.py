"""Compatibility alias for the M7.1 value types.

Non-responsibility: does not duplicate value-type definitions.
"""

from __future__ import annotations

import sys

from ..planner_bench.path_audit import types as _implementation

sys.modules[__name__] = _implementation
