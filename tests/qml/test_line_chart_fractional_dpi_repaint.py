# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Fractional-DPI line repaint regressions. 分数DPI折线图重绘回归。"""

import os
import subprocess
import sys

import pytest
from PySide6.QtQml import QQmlEngine, QQmlExpression
from PySide6.QtTest import QSignalSpy

from test_chart_runtime_performance import (
    ROOT,
    _animated_canvases,
    _evaluate,
    _loaders,
    _pump,
    windowed_chart_scene,
)


def _maximum_column_pixel_difference(first, second) -> int:
    assert first.size() == second.size()
    maximum = 0
    for x in range(first.width()):
        difference = sum(
            first.pixel(x, y) != second.pixel(x, y)
            for y in range(first.height())
        )
        maximum = max(maximum, difference)
    return maximum


def test_line_hover_partial_repaint_matches_full_repaint(windowed_chart_scene):
    chart, warnings = windowed_chart_scene
    chart.setProperty("animated", False)
    chart.setProperty(
        "chartData",
        [
            {"label": label}
            for label in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
        ],
    )
    chart.setProperty(
        "series",
        [
            {"name": "Highest", "values": [10, 11, 13, 11, 12, 12, 9]},
            {"name": "Lowest", "values": [1, -2, 2, 5, 3, 2, 0]},
        ],
    )
    chart.setProperty("showAreaGradient", True)
    _pump(50)

    line_content = _loaders(chart)["lineContentLoader"].property("item")
    assert line_content is not None
    canvas = _animated_canvases(line_content)[0]
    painted = QSignalSpy(canvas.painted)
    full_paint = QQmlExpression(
        QQmlEngine.contextForObject(canvas), canvas, "(requestPaint(), true)"
    )
    assert _evaluate(full_paint)
    assert painted.wait(1_000)

    line_content.setProperty("hoveredSeriesIndex", 0)
    for index in range(7):
        line_content.setProperty("hoveredIndex", index)
        assert painted.wait(1_000)
    line_content.setProperty("hoveredIndex", -1)
    assert painted.wait(1_000)

    partial_image = chart.window().grabWindow()
    assert _evaluate(full_paint)
    assert painted.wait(1_000)
    full_image = chart.window().grabWindow()
    ratio = chart.window().devicePixelRatio()
    quantum = line_content.property("_dirtyPixelQuantum")
    assert quantum >= 1
    assert ratio * quantum == pytest.approx(round(ratio * quantum))
    assert all(
        ratio * candidate != pytest.approx(round(ratio * candidate))
        for candidate in range(1, quantum)
    )
    assert partial_image == full_image or (
        _maximum_column_pixel_difference(partial_image, full_image) <= 8
    )
    assert warnings == []


def test_line_hover_partial_repaint_at_fractional_dpi():
    environment = os.environ.copy()
    environment["QT_SCALE_FACTOR"] = "1.5"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "test_process.py"),
            "--qt-platform",
            "offscreen",
            "--timeout",
            "60",
            "--",
            sys.executable,
            "-m",
            "pytest",
            f"{__file__}::test_line_hover_partial_repaint_matches_full_repaint",
            "-q",
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
        check=False,
    )
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, output
    if sys.platform == "win32":
        assert "visible_windows=0 / job_active_processes=0" in output
