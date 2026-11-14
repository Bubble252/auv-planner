"""Compatibility alias for the M7.1 artifact writer.

Non-responsibility: does not duplicate artifact-writing logic.
"""

from __future__ import annotations

import sys

from ..planner_bench.path_audit import io as _implementation

sys.modules[__name__] = _implementation
