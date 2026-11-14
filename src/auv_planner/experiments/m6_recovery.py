"""Compatibility alias for the M6 recovery experiment module.

Non-responsibility: does not duplicate recovery experiment logic.
"""

from __future__ import annotations

import sys

from .validation import recovery as _implementation

sys.modules[__name__] = _implementation
