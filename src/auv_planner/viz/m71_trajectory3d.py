"""Interactive 3D review pages for persisted M7.1 planner trajectories.

This module is deliberately read-only with respect to planning data. It consumes
``trajectories.csv``, ``points.csv`` and ``paths.csv`` plus the authoritative
scenario definitions, then writes standalone Plotly HTML review pages.
"""

from __future__ import annotations

import csv
import html
import json
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from math import cos, pi, sin
from pathlib import Path
from typing import Literal

import numpy as np
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs

from auv_core.contracts import Obstacle, ScenarioConfig
from ..experiments.m7_1 import m71_case_specs

Point3 = tuple[float, float, float]
PlotlyJSMode = Literal["directory", "inline", "cdn"]

_PLANNER_COLORS = {
    "astar": "#1f4e79",
    "rrt_star": "#c55a11",
}
_PLANNER_LABELS = {
    "astar": "A*",
    "rrt_star": "RRT*",
}
_STATUS_COLORS = {
    "valid": "#2e8b57",
    "invalid": "#c0392b",
    "unknown": "#d68910",
}
_STATUS_SYMBOLS = {
    "valid": "circle",
    "invalid": "x",
    "unknown": "diamond",
}


def _finite_float(value: object, name: str) -> float:
    try:
        result = float(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not np.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _required_text(value: object, name: str) -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        raise ValueError(f"{name} must be a non-empty string")
    return text


def _display_point(point: Point3) -> Point3:
    return (point[0], point[1], -point[2])


@dataclass(frozen=True)
class M71TrajectoryPoint:
    index: int
    t_s: float
    position_ned_m: Point3


@dataclass(frozen=True)
class M71TrajectorySample:
    t_s: float
    position_ned_m: Point3
    clearance_m: float
    full_status: str
    online_status: str
    failure_source: str


@dataclass(frozen=True)
class M71PathSummary:
    coverage_ratio: float
    max_uncovered_s: float
    path_length_m: float
    duration_s: float
    min_clearance_m: float
    valid_points: int
    invalid_points: int
    unknown_points: int


@dataclass(frozen=True)
class M71Trajectory:
    planner: str
    variant: str
    points: tuple[M71TrajectoryPoint, ...]


@dataclass(frozen=True)
class M71CaseView:
    case_name: str
    scenario: ScenarioConfig
    trajectories: tuple[M71Trajectory, ...]
    samples: tuple[tuple[str, tuple[M71TrajectorySample, ...]], ...]
    summaries: tuple[tuple[str, M71PathSummary], ...]

    @property
    def planners(self) -> tuple[str, ...]:
        return tuple(planner for planner, _ in self.summaries)

    def summary_for(self, planner: str) -> M71PathSummary:
        for name, summary in self.summaries:
            if name == planner:
                return summary
        raise KeyError(f"no path summary for planner {planner}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _baseline_rows(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("variant", "baseline") == "baseline"]


def _trajectory_by_key(
    rows: Iterable[dict[str, str]],
) -> dict[tuple[str, str], tuple[M71TrajectoryPoint, ...]]:
    grouped: defaultdict[tuple[str, str], list[M71TrajectoryPoint]] = defaultdict(list)
    for row in _baseline_rows(rows):
        case = _required_text(row.get("case"), "trajectories.case")
        planner = _required_text(row.get("planner"), "trajectories.planner")
        point = M71TrajectoryPoint(
            index=int(_finite_float(row.get("index"), "trajectories.index")),
            t_s=_finite_float(row.get("t_s"), "trajectories.t_s"),
            position_ned_m=(
                _finite_float(row.get("x_m"), "trajectories.x_m"),
                _finite_float(row.get("y_m"), "trajectories.y_m"),
                _finite_float(row.get("z_m"), "trajectories.z_m"),
            ),
        )
        grouped[(case, planner)].append(point)
    return {
        key: tuple(sorted(points, key=lambda point: (point.index, point.t_s)))
        for key, points in grouped.items()
    }


def _samples_by_key(
    rows: Iterable[dict[str, str]],
) -> dict[tuple[str, str], tuple[M71TrajectorySample, ...]]:
    grouped: defaultdict[tuple[str, str], list[M71TrajectorySample]] = defaultdict(list)
    for row in _baseline_rows(rows):
        case = _required_text(row.get("case"), "points.case")
        planner = _required_text(row.get("planner"), "points.planner")
        grouped[(case, planner)].append(
            M71TrajectorySample(
                t_s=_finite_float(row.get("t_s"), "points.t_s"),
                position_ned_m=(
                    _finite_float(row.get("x_m"), "points.x_m"),
                    _finite_float(row.get("y_m"), "points.y_m"),
                    _finite_float(row.get("z_m"), "points.z_m"),
                ),
                clearance_m=_finite_float(row.get("clearance_m"), "points.clearance_m"),
                full_status=_required_text(row.get("full_status"), "points.full_status"),
                online_status=str(row.get("online_status", "")).strip(),
                failure_source=str(row.get("failure_source", "")).strip(),
            )
        )
    return {
        key: tuple(sorted(samples, key=lambda sample: sample.t_s))
        for key, samples in grouped.items()
    }


def _summaries_by_key(rows: Iterable[dict[str, str]]) -> dict[tuple[str, str], M71PathSummary]:
    summaries: dict[tuple[str, str], M71PathSummary] = {}
    for row in _baseline_rows(rows):
        case = _required_text(row.get("case"), "paths.case")
        planner = _required_text(row.get("planner"), "paths.planner")
        summaries[(case, planner)] = M71PathSummary(
            coverage_ratio=_finite_float(row.get("coverage_ratio"), "paths.coverage_ratio"),
            max_uncovered_s=_finite_float(row.get("max_uncovered_s"), "paths.max_uncovered_s"),
            path_length_m=_finite_float(row.get("path_length_m"), "paths.path_length_m"),
            duration_s=_finite_float(row.get("duration_s"), "paths.duration_s"),
            min_clearance_m=_finite_float(row.get("min_clearance_m"), "paths.min_clearance_m"),
            valid_points=int(_finite_float(row.get("valid_points"), "paths.valid_points")),
            invalid_points=int(_finite_float(row.get("invalid_points"), "paths.invalid_points")),
            unknown_points=int(_finite_float(row.get("unknown_points"), "paths.unknown_points")),
        )
    return summaries


def load_m71_case_views(run_dir: Path | str) -> tuple[M71CaseView, ...]:
    """Load baseline trajectories for every case present in one M7.1 run."""

    root = Path(run_dir)
    trajectories = _trajectory_by_key(_read_csv(root / "trajectories.csv"))
    samples = _samples_by_key(_read_csv(root / "points.csv"))
    summaries = _summaries_by_key(_read_csv(root / "paths.csv"))
    scenarios = {spec.name: spec.scenario for spec in m71_case_specs()}

    cases = sorted({case for case, _ in trajectories})
    views: list[M71CaseView] = []
    for case in cases:
        if case not in scenarios:
            raise KeyError(f"no authoritative scenario definition for M7.1 case {case}")
        case_trajectories = tuple(
            M71Trajectory(
                planner=planner,
                variant="baseline",
                points=trajectories[(case, planner)],
            )
            for planner in ("astar", "rrt_star")
            if (case, planner) in trajectories
        )
        case_summaries = tuple(
            (planner, summaries[(case, planner)])
            for planner in ("astar", "rrt_star")
            if (case, planner) in summaries
        )
        case_samples = tuple(
            (planner, samples.get((case, planner), ()))
            for planner in ("astar", "rrt_star")
            if (case, planner) in samples
        )
        if not case_trajectories or not case_summaries:
            continue
        views.append(
            M71CaseView(
                case_name=case,
                scenario=scenarios[case],
                trajectories=case_trajectories,
                samples=case_samples,
                summaries=case_summaries,
            )
        )
    return tuple(views)


def _path_trace(trajectory: M71Trajectory) -> go.Scatter3d:
    planner = trajectory.planner
    points = tuple(_display_point(point.position_ned_m) for point in trajectory.points)
    labels = tuple(
        (
            f"{_PLANNER_LABELS[planner]} path<br>"
            f"t={point.t_s:.2f} s<br>"
            f"NED=({point.position_ned_m[0]:.3f}, "
            f"{point.position_ned_m[1]:.3f}, {point.position_ned_m[2]:.3f})"
        )
        for point in trajectory.points
    )
    return go.Scatter3d(
        x=[point[0] for point in points],
        y=[point[1] for point in points],
        z=[point[2] for point in points],
        mode="lines+markers",
        line={
            "color": _PLANNER_COLORS[planner],
            "width": 7,
            "dash": "solid" if planner == "astar" else "dash",
        },
        marker={
            "color": _PLANNER_COLORS[planner],
            "size": 4,
            "symbol": "circle",
        },
        name=f"{_PLANNER_LABELS[planner]} planner path",
        legendgroup=planner,
        text=list(labels),
        hovertemplate="%{text}<extra></extra>",
    )


def _sample_trace(
    planner: str,
    samples: Sequence[M71TrajectorySample],
) -> go.Scatter3d:
    display = tuple(_display_point(sample.position_ned_m) for sample in samples)
    colors = tuple(_STATUS_COLORS.get(sample.full_status, "#555555") for sample in samples)
    symbols = tuple(_STATUS_SYMBOLS.get(sample.full_status, "circle") for sample in samples)
    labels = tuple(
        (
            f"{_PLANNER_LABELS[planner]} certificate sample<br>"
            f"t={sample.t_s:.2f} s<br>"
            f"NED=({sample.position_ned_m[0]:.3f}, "
            f"{sample.position_ned_m[1]:.3f}, {sample.position_ned_m[2]:.3f})<br>"
            f"clearance={sample.clearance_m:.3f} m<br>"
            f"full={sample.full_status}"
            + (f"<br>online={sample.online_status}" if sample.online_status else "")
            + (f"<br>failure sources={sample.failure_source}" if sample.failure_source else "")
        )
        for sample in samples
    )
    return go.Scatter3d(
        x=[point[0] for point in display],
        y=[point[1] for point in display],
        z=[point[2] for point in display],
        mode="markers",
        marker={"color": list(colors), "size": 6, "symbol": list(symbols)},
        name=f"{_PLANNER_LABELS[planner]} certificate samples",
        legendgroup=planner,
        text=list(labels),
        hovertemplate="%{text}<extra></extra>",
    )


def _box_geometry(
    obstacle: Obstacle,
) -> tuple[tuple[Point3, ...], tuple[tuple[int, int, int], ...]]:
    if obstacle.half_extents_m is None:
        raise ValueError(f"box obstacle {obstacle.obstacle_id} has no half_extents_m")
    center = np.asarray(obstacle.center_ned_m, dtype=np.float64)
    half = np.asarray(obstacle.half_extents_m, dtype=np.float64)
    vertices = tuple(
        (
            float(center[0] + sx * half[0]),
            float(center[1] + sy * half[1]),
            float(center[2] + sz * half[2]),
        )
        for sx, sy, sz in (
            (-1, -1, -1),
            (1, -1, -1),
            (1, 1, -1),
            (-1, 1, -1),
            (-1, -1, 1),
            (1, -1, 1),
            (1, 1, 1),
            (-1, 1, 1),
        )
    )
    faces = (
        (0, 1, 2),
        (0, 2, 3),
        (4, 6, 5),
        (4, 7, 6),
        (0, 5, 1),
        (0, 4, 5),
        (1, 6, 2),
        (1, 5, 6),
        (2, 7, 3),
        (2, 6, 7),
        (3, 4, 0),
        (3, 7, 4),
    )
    return vertices, faces


def _cylinder_geometry(
    obstacle: Obstacle,
) -> tuple[tuple[Point3, ...], tuple[tuple[int, int, int], ...]]:
    if obstacle.radius_m is None or obstacle.height_m is None:
        raise ValueError(f"cylinder obstacle {obstacle.obstacle_id} has incomplete dimensions")
    center = np.asarray(obstacle.center_ned_m, dtype=np.float64)
    radius = float(obstacle.radius_m)
    height = float(obstacle.height_m)
    count = 24
    lower = tuple(
        (
            float(center[0] + radius * cos(2.0 * pi * index / count)),
            float(center[1] + radius * sin(2.0 * pi * index / count)),
            float(center[2] - height / 2.0),
        )
        for index in range(count)
    )
    upper = tuple(
        (
            float(center[0] + radius * cos(2.0 * pi * index / count)),
            float(center[1] + radius * sin(2.0 * pi * index / count)),
            float(center[2] + height / 2.0),
        )
        for index in range(count)
    )
    vertices = (
        lower
        + upper
        + (
            (float(center[0]), float(center[1]), float(center[2] - height / 2.0)),
            (float(center[0]), float(center[1]), float(center[2] + height / 2.0)),
        )
    )
    lower_center = 2 * count
    upper_center = lower_center + 1
    faces: list[tuple[int, int, int]] = []
    for index in range(count):
        next_index = (index + 1) % count
        faces.extend(
            (
                (index, next_index, count + index),
                (count + index, next_index, count + next_index),
                (lower_center, next_index, index),
                (upper_center, count + index, count + next_index),
            )
        )
    return vertices, tuple(faces)


def _sphere_geometry(
    obstacle: Obstacle,
) -> tuple[tuple[Point3, ...], tuple[tuple[int, int, int], ...]]:
    if obstacle.radius_m is None:
        raise ValueError(f"sphere obstacle {obstacle.obstacle_id} has no radius_m")
    center = np.asarray(obstacle.center_ned_m, dtype=np.float64)
    radius = float(obstacle.radius_m)
    latitude_count = 10
    longitude_count = 20
    vertices: list[Point3] = []
    for latitude in range(latitude_count + 1):
        theta = pi * latitude / latitude_count
        for longitude in range(longitude_count):
            phi = 2.0 * pi * longitude / longitude_count
            vertices.append(
                (
                    float(center[0] + radius * sin(theta) * cos(phi)),
                    float(center[1] + radius * sin(theta) * sin(phi)),
                    float(center[2] + radius * cos(theta)),
                )
            )
    faces: list[tuple[int, int, int]] = []
    row = longitude_count
    for latitude in range(latitude_count):
        for longitude in range(longitude_count):
            next_longitude = (longitude + 1) % longitude_count
            a = latitude * row + longitude
            b = latitude * row + next_longitude
            c = (latitude + 1) * row + longitude
            d = (latitude + 1) * row + next_longitude
            faces.extend(((a, b, c), (b, d, c)))
    return tuple(vertices), tuple(faces)


def _obstacle_trace(obstacle: Obstacle) -> go.Mesh3d | None:
    if obstacle.kind == "box":
        vertices, faces = _box_geometry(obstacle)
    elif obstacle.kind == "cylinder":
        vertices, faces = _cylinder_geometry(obstacle)
    elif obstacle.kind == "sphere":
        vertices, faces = _sphere_geometry(obstacle)
    else:
        return None
    display = tuple(_display_point(point) for point in vertices)
    return go.Mesh3d(
        x=[point[0] for point in display],
        y=[point[1] for point in display],
        z=[point[2] for point in display],
        i=[face[0] for face in faces],
        j=[face[1] for face in faces],
        k=[face[2] for face in faces],
        color="rgb(145, 150, 155)",
        opacity=0.28,
        flatshading=True,
        name=obstacle.obstacle_id,
        showlegend=False,
        text=[obstacle.obstacle_id],
        hovertemplate="%{text}<extra></extra>",
    )


def _case_title(case: M71CaseView) -> str:
    parts = []
    for planner in case.planners:
        summary = case.summary_for(planner)
        parts.append(
            f"{_PLANNER_LABELS[planner]} coverage {100.0 * summary.coverage_ratio:.1f}% "
            f"(max uncovered {summary.max_uncovered_s:.2f} s)"
        )
    return f"{case.case_name} · {case.scenario.name}<br><sup>{' | '.join(parts)}</sup>"


def build_case_figure(case: M71CaseView) -> go.Figure:
    traces: list[go.Scatter3d | go.Mesh3d] = []
    for trajectory in case.trajectories:
        traces.append(_path_trace(trajectory))
    for planner, samples in case.samples:
        if samples:
            traces.append(_sample_trace(planner, samples))
    for obstacle in case.scenario.world.obstacle_map.obstacles:
        trace = _obstacle_trace(obstacle)
        if trace is not None:
            traces.append(trace)

    start_array = np.asarray(case.scenario.start.position_ned_m, dtype=np.float64)
    goal_array = np.asarray(case.scenario.goal_ned_m, dtype=np.float64)
    start = _display_point((float(start_array[0]), float(start_array[1]), float(start_array[2])))
    goal = _display_point((float(goal_array[0]), float(goal_array[1]), float(goal_array[2])))
    traces.extend(
        (
            go.Scatter3d(
                x=[start[0]],
                y=[start[1]],
                z=[start[2]],
                mode="markers",
                marker={"color": "#1565c0", "size": 9, "symbol": "diamond"},
                name="start",
                text=["start"],
                hovertemplate="%{text}<extra></extra>",
            ),
            go.Scatter3d(
                x=[goal[0]],
                y=[goal[1]],
                z=[goal[2]],
                mode="markers",
                marker={"color": "#6a1b9a", "size": 9, "symbol": "cross"},
                name="goal",
                text=["goal"],
                hovertemplate="%{text}<extra></extra>",
            ),
        )
    )

    bounds = case.scenario.world.obstacle_map.bounds_ned_m
    figure = go.Figure(data=traces)
    figure.update_layout(
        title={"text": _case_title(case), "x": 0.5},
        template="plotly_white",
        height=850,
        margin={"l": 0, "r": 0, "t": 92, "b": 0},
        hovermode="closest",
        legend={"x": 0.01, "y": 0.99, "bgcolor": "rgba(255,255,255,0.82)"},
        scene={
            "xaxis": {
                "title": "NED x [m]",
                "range": [float(bounds[0, 0]), float(bounds[0, 1])],
                "backgroundcolor": "rgb(245,245,245)",
                "gridcolor": "white",
            },
            "yaxis": {
                "title": "NED y [m]",
                "range": [float(bounds[1, 0]), float(bounds[1, 1])],
                "backgroundcolor": "rgb(245,245,245)",
                "gridcolor": "white",
            },
            "zaxis": {
                "title": "Altitude [m] (up positive)",
                "range": [float(-bounds[2, 1]), float(-bounds[2, 0])],
                "backgroundcolor": "rgb(245,245,245)",
                "gridcolor": "white",
            },
            "aspectmode": "data",
            "dragmode": "orbit",
            "camera": {"eye": {"x": 1.65, "y": 1.55, "z": 1.15}},
        },
        annotations=[
            {
                "text": (
                    "Drag to rotate · wheel to zoom · right-drag to pan<br>"
                    "Certificate markers: green circle = valid, red x = invalid, "
                    "orange diamond = unknown. A red x is not a geometric collision."
                ),
                "xref": "paper",
                "yref": "paper",
                "x": 0.01,
                "y": 0.01,
                "showarrow": False,
                "align": "left",
                "font": {"size": 11, "color": "rgb(80,80,80)"},
            }
        ],
    )
    return figure


def _ensure_plotlyjs(directory: Path) -> None:
    path = directory / "plotly.min.js"
    if not path.exists():
        path.write_text(get_plotlyjs(), encoding="utf-8")


def _write_case_html(
    figure: go.Figure,
    output_path: Path,
    *,
    plotlyjs_mode: PlotlyJSMode,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if plotlyjs_mode == "directory":
        _ensure_plotlyjs(output_path.parent)
    figure.write_html(
        str(output_path),
        include_plotlyjs=plotlyjs_mode,
        full_html=True,
        auto_open=False,
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "scrollZoom": True,
            "showTips": True,
        },
    )


def _index_html(cases: Sequence[M71CaseView]) -> str:
    cards: list[str] = []
    for case in cases:
        summaries = []
        for planner in case.planners:
            summary = case.summary_for(planner)
            summaries.append(
                f"<li><b>{html.escape(_PLANNER_LABELS[planner])}</b>: "
                f"coverage {100.0 * summary.coverage_ratio:.1f}%, "
                f"max gap {summary.max_uncovered_s:.2f} s, "
                f"clearance {summary.min_clearance_m:.3f} m</li>"
            )
        filename = f"{html.escape(case.case_name)}.html"
        cards.append(
            f"""
            <section class="card">
              <div class="card-head">
                <div>
                  <h2>{html.escape(case.case_name)}</h2>
                  <p class="muted">{html.escape(case.scenario.name)}</p>
                </div>
                <a class="open" href="{filename}">单独打开 3D</a>
              </div>
              <ul>{"".join(summaries)}</ul>
              <iframe src="{filename}" loading="lazy" title="{html.escape(case.case_name)}"></iframe>
            </section>
            """
        )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>M7.1 全局规划 3D 轨迹审阅</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: Inter, "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;
      background: #f3f5f7;
      color: #18212b;
    }}
    body {{ margin: 0; padding: 24px; }}
    header {{ max-width: 1500px; margin: 0 auto 20px; }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    .notice {{
      background: #fff8e1; border-left: 5px solid #d68910;
      padding: 12px 16px; border-radius: 6px; max-width: 1500px; margin: 0 auto 22px;
    }}
    .grid {{ max-width: 1500px; margin: 0 auto; display: grid; gap: 20px; }}
    .card {{
      background: white; border: 1px solid #dfe4e8; border-radius: 10px;
      padding: 16px; box-shadow: 0 2px 10px rgba(20, 30, 40, .05);
    }}
    .card-head {{ display: flex; justify-content: space-between; gap: 16px; align-items: start; }}
    h2 {{ margin: 0 0 4px; font-size: 20px; }}
    .muted {{ margin: 0; color: #66727e; }}
    ul {{ margin: 10px 0 14px; padding-left: 22px; line-height: 1.7; }}
    .open {{
      white-space: nowrap; text-decoration: none; color: white; background: #1f4e79;
      border-radius: 6px; padding: 9px 12px; font-weight: 600;
    }}
    iframe {{ width: 100%; height: 850px; border: 1px solid #e3e7ea; border-radius: 6px; }}
    code {{ background: #edf1f4; padding: 2px 5px; border-radius: 4px; }}
  </style>
</head>
<body>
  <header>
    <h1>M7.1 全局规划 3D 轨迹审阅</h1>
    <p>真实 A* / RRT* 规划折线，叠加每秒证书采样点与冻结场景障碍物。支持拖动旋转、滚轮缩放、右键平移和图例开关。</p>
  </header>
  <div class="notice">
    红色叉号表示 <code>full_status=invalid</code>，即当前保守故障集下证书查询失败，
    不是几何碰撞。三维轨迹与障碍物均来自 M7.1 冻结结果。
  </div>
  <main class="grid">
    {"".join(cards)}
  </main>
</body>
</html>
"""


def render_m71_3d_html(
    run_dir: Path | str,
    output_dir: Path | str,
    *,
    plotlyjs_mode: PlotlyJSMode = "directory",
) -> tuple[Path, ...]:
    """Render one 3D page per case plus a linked index page."""

    if plotlyjs_mode not in {"directory", "inline", "cdn"}:
        raise ValueError(f"unsupported plotlyjs_mode: {plotlyjs_mode}")
    cases = load_m71_case_views(run_dir)
    if not cases:
        raise ValueError(f"no baseline M7.1 trajectories found in {run_dir}")
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    if plotlyjs_mode == "directory":
        _ensure_plotlyjs(root)

    output_paths: list[Path] = []
    for case in cases:
        output_path = root / f"{case.case_name}.html"
        _write_case_html(
            build_case_figure(case),
            output_path,
            plotlyjs_mode=plotlyjs_mode,
        )
        output_paths.append(output_path)

    index_path = root / "index.html"
    index_path.write_text(_index_html(cases), encoding="utf-8")
    output_paths.append(index_path)
    manifest = {
        "schema_version": 1,
        "source_run_dir": str(Path(run_dir).resolve()),
        "cases": [case.case_name for case in cases],
        "pages": [path.name for path in output_paths],
        "plotlyjs_mode": plotlyjs_mode,
        "warning": (
            "Trajectories are baseline A*/RRT* planner outputs from M7.1. "
            "Invalid certificate markers are not geometric collisions."
        ),
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    output_paths.append(root / "manifest.json")
    return tuple(output_paths)


__all__ = [
    "M71CaseView",
    "M71PathSummary",
    "M71Trajectory",
    "M71TrajectoryPoint",
    "M71TrajectorySample",
    "PlotlyJSMode",
    "build_case_figure",
    "load_m71_case_views",
    "render_m71_3d_html",
]
