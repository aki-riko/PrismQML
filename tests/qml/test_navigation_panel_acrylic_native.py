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
        "120",
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
        timeout=150,
        check=False,
    )


def _changed(pair: dict[str, object], name: str) -> bool:
    return pair["on"][name] != pair["off"][name]


def _pixel_delta(pair: dict[str, object], name: str) -> int:
    return sum(
        abs(on_channel - off_channel)
        for on_channel, off_channel in zip(
            pair["on"][name][:3], pair["off"][name][:3]
        )
    )


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


def _assert_lifecycle_contract(report: dict[str, object]) -> None:
    assert report["backend"] == "Direct3D11"
    assert report["window_visible"] is False
    assert report["warnings"] == []
    for state in STATES:
        assert report[state]["expanded"] is True
        _assert_corner_contract(report[state])
    _assert_vertical_colors(report["initial"], "red", "green")
    _assert_vertical_colors(report["updated"], "blue", "red")
    for state in ("resized", "dark", "reexpanded"):
        _assert_vertical_colors(report[state], "red", "green")
    assert report["initial"]["size"] != report["resized"]["size"]


def _assert_gallery_contract(gallery: dict[str, object]) -> None:
    assert gallery["backend"] == "Direct3D11"
    assert gallery["window_visible"] is False
    assert gallery["window_class"] == "WindowsSplit"
    assert gallery["settings_page_loaded"] is True
    assert gallery["expanded"] is True
    assert gallery["warnings"] == []
    assert gallery["acrylic_source"] == "collapsed_qml_composite_not_desktop_dwm"
    shadow = gallery["shadow"]
    for name in ("corner_top_inset", "corner_bottom_inset"):
        assert _changed(shadow, name), (name, shadow)
    assert not _changed(shadow, "edge_center_inside"), shadow
    assert _changed(shadow, "edge_center_outside"), shadow
    center_delta = _pixel_delta(shadow, "edge_center_outside")
    assert 0 < _pixel_delta(shadow, "edge_top_outside") < center_delta, shadow
    assert 0 < _pixel_delta(shadow, "edge_bottom_outside") < center_delta, shadow
    acrylic = gallery["acrylic"]
    for name in ("corner_top_inset", "corner_bottom_inset"):
        assert not _changed(acrylic, name), (name, acrylic)
    for name in ("body_upper", "body_lower"):
        assert _changed(acrylic, name), (name, acrylic)


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
    _assert_lifecycle_contract(report)
    _assert_gallery_contract(report["gallery_shell"])
    assert "visible_windows=0 / job_active_processes=0" in output
