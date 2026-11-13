"""Stable JSON document rendering shared by planner entry points."""

from __future__ import annotations

import json
from pathlib import Path


def dumps_json_document(payload: object) -> str:
    """Render a deterministic JSON document with one trailing newline."""

    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_json_document(path: Path | str, payload: object) -> Path:
    """Write a deterministic JSON document without creating parent directories."""

    output_path = Path(path)
    output_path.write_text(dumps_json_document(payload), encoding="utf-8")
    return output_path
