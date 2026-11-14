"""Compatibility alias for the M7.1 runner.

Non-responsibility: does not duplicate runner logic.
"""

from __future__ import annotations

import sys

from ..planner_bench.path_audit import runner as _implementation

sys.modules[__name__] = _implementation
