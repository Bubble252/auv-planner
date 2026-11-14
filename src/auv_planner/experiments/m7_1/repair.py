"""Compatibility alias for the M7.1 repair implementation.

Non-responsibility: does not duplicate repair logic.
"""

from __future__ import annotations

import sys

from ..planner_bench.path_audit import repair as _implementation

sys.modules[__name__] = _implementation
