"""Render interactive 3D HTML review pages for the frozen M7.1 trajectories."""

from __future__ import annotations

import argparse
from pathlib import Path

from auv_planner.viz import render_m71_3d_html


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render interactive Plotly 3D pages for M7.1 baseline trajectories."
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=Path("outputs/m7_1"),
        help="Directory containing trajectories.csv, points.csv and paths.csv.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/m7_1/3d"),
        help="Directory for generated HTML pages and shared Plotly JavaScript.",
    )
    parser.add_argument(
        "--plotlyjs",
        choices=("directory", "inline", "cdn"),
        default="directory",
        help="How generated HTML pages should load Plotly.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    outputs = render_m71_3d_html(
        args.run_dir,
        args.output_dir,
        plotlyjs_mode=args.plotlyjs,
    )
    for path in outputs:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
