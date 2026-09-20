# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Native acrylic navigation pixel regressions. 原生亚克力导航像素回归。"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts" / "test_process.py"
PROBE = ROOT / "tests" / "qml" / "navigation_panel_acrylic_native_probe.py"
STATES = ("initial", "updated", "resized", "dark", "reexpanded")


def _run_probe(report_path: Path) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(RUNNER),
        "--qt-platform",
        "windows",
        "--timeout",
        "60",
        "--",
        sys.executable,
        str(PROBE),
        "--output",
        str(report_path),
    ]
    return subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
        check=False,
    )


def _changed(pair: dict[str, object], name: str) -> bool:
    return pair["on"][name] != pair["off"][name]


def _assert_corner_contract(pair: dict[str, object]) -> None:
    for name in ("top_outside", "bottom_outside"):
        assert pair["on"][name] == pair["off"][name], (name, pair)
    for name in ("top_inside", "bottom_inside", "upper_center", "lower_center"):
        assert _changed(pair, name), (name, pair)


def _assert_vertical_colors(pair: dict[str, object], upper: str, lower: str) -> None:
    upper_color = pair["on"]["upper_center"]
    lower_color = pair["on"]["lower_center"]
    channels = {"red": 0, "green": 1, "blue": 2}
    upper_index = channels[upper]
    lower_index = channels[lower]
    assert upper_color[upper_index] > max(
        value for index, value in enumerate(upper_color[:3]) if index != upper_index
    ), upper_color
    assert lower_color[lower_index] > max(
        value for index, value in enumerate(lower_color[:3]) if index != lower_index
    ), lower_color


@pytest.mark.skipif(sys.platform != "win32", reason="D3D11 requires Windows")
def test_navigation_panel_acrylic_native_rounding_and_lifecycle(tmp_path):
    """The hidden native scene keeps acrylic inside the panel silhouette.

    隐藏的原生场景在换源、缩放和折叠重展后仍将亚克力限制在面板轮廓内。
    """
    report_path = tmp_path / "navigation-panel-acrylic-native.json"
    result = _run_probe(report_path)
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, output
    assert report_path.exists(), output
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["backend"] == "Direct3D11"
    assert report["window_visible"] is False
    assert report["warnings"] == []
    for state in STATES:
        assert report[state]["expanded"] is True
        _assert_corner_contract(report[state])
    _assert_vertical_colors(report["initial"], "red", "green")
    _assert_vertical_colors(report["updated"], "blue", "red")
    _assert_vertical_colors(report["resized"], "red", "green")
    _assert_vertical_colors(report["dark"], "red", "green")
    _assert_vertical_colors(report["reexpanded"], "red", "green")
    assert report["initial"]["size"] != report["resized"]["size"]
    assert "visible_windows=0 / job_active_processes=0" in output
