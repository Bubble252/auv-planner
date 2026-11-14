"""Byte-stable CSV writers shared by experiment artifact modules."""

from __future__ import annotations

import csv
from collections.abc import Sequence
from pathlib import Path
from typing import Any


def write_csv_allow_empty(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    """Write first-row fields, preserving an empty result as an empty file."""
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
