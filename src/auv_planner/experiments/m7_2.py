"""Compatibility alias for the M7.2 planner-comparison module.

Non-responsibility: does not duplicate comparison logic.
"""

from __future__ import annotations

import sys

from .planner_bench import planner_comparison as _implementation

sys.modules[__name__] = _implementation
