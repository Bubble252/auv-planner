"""Compatibility alias for the M7 recoverability-budget module.

Non-responsibility: does not duplicate budget experiment logic.
"""

from __future__ import annotations

import sys

from .planner_bench import budget as _implementation

sys.modules[__name__] = _implementation
