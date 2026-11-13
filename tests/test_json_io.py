from __future__ import annotations

import json
from pathlib import Path

import pytest

from auv_planner._json import dumps_json_document, write_json_document


def test_json_document_matches_stable_renderer() -> None:
    payload = {"z": 1, "a": "é"}

    assert dumps_json_document(payload) == json.dumps(payload, indent=2, sort_keys=True) + "\n"


def test_json_document_writes_utf8_and_returns_path(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"

    written = write_json_document(path, {"b": 2, "a": 1})

    assert written == path
    assert path.read_text(encoding="utf-8") == '{\n  "a": 1,\n  "b": 2\n}\n'


def test_json_document_does_not_create_parent_directories(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        write_json_document(tmp_path / "missing" / "manifest.json", {"a": 1})


def test_json_document_propagates_serialization_errors() -> None:
    with pytest.raises(TypeError):
        dumps_json_document({"not_json": object()})
