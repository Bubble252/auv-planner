"""Compatibility alias for the M5 model-validation module.

Non-responsibility: does not duplicate validation logic.
"""

from __future__ import annotations

import sys

from .validation import model_validation as _implementation

sys.modules[__name__] = _implementation
