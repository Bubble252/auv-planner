"""Compatibility alias for the M4 closed-loop experiment module.

Non-responsibility: does not duplicate experiment logic.
"""

from __future__ import annotations

import sys

from .validation import closed_loop as _implementation

sys.modules[__name__] = _implementation
