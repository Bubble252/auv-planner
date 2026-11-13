from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from auv_planner.experiments.m7_1 import _write_csv as write_m7_1_csv
from auv_planner.experiments.m7_2 import _write_csv as write_m7_2_csv

Writer = Callable[[Path, list[dict[str, object]]], None]
WRITERS = pytest.mark.parametrize(
    "writer",
    [write_m7_1_csv, write_m7_2_csv],
    ids=["m7_1", "m7_2"],
)


@WRITERS
def test_m7_writers_use_first_row_fields_and_csv_newlines(tmp_path: Path, writer: Writer) -> None:
    path = tmp_path / "paths.csv"
    rows = [
        {"alpha": "plain", "beta": "1", "note": "comma,value"},
        {"alpha": 'quote"value', "beta": "2", "note": "line\nbreak"},
    ]

    writer(path, rows)

    assert path.read_bytes() == (
        b'alpha,beta,note\r\nplain,1,"comma,value"\r\n"quote""value",2,"line\nbreak"\r\n'
    )


@WRITERS
def test_m7_writers_keep_empty_csv_as_valid_artifact(tmp_path: Path, writer: Writer) -> None:
    path = tmp_path / "empty.csv"

    writer(path, [])

    assert path.read_bytes() == b""


@WRITERS
def test_m7_writers_keep_python_repr_for_list_values(tmp_path: Path, writer: Writer) -> None:
    path = tmp_path / "values.csv"

    writer(path, [{"values": [1, 2], "flag": True}])

    assert path.read_bytes() == b'values,flag\r\n"[1, 2]",True\r\n'


@WRITERS
def test_m7_writers_do_not_create_parent_directories(tmp_path: Path, writer: Writer) -> None:
    path = tmp_path / "missing" / "paths.csv"

    with pytest.raises(FileNotFoundError):
        writer(path, [{"alpha": "plain"}])
