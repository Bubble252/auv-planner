"""Compatibility alias for the M7.1 audit implementation.

Non-responsibility: does not duplicate audit logic.
"""

from __future__ import annotations

import sys

from ..planner_bench.path_audit import audit as _implementation

sys.modules[__name__] = _implementation
