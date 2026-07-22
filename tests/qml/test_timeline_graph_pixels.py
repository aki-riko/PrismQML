# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Timeline graph pixel continuity regressions. 时间线图像素连续性回归。"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TEST_PROCESS = ROOT / "scripts" / "test_process.py"
BOUNDARY_PROBE = r'''
from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtWidgets import QApplication

from prismqml import register_types


root = Path.cwd()
app = QApplication([])
engine = QQmlApplicationEngine()
warnings = []
engine.warnings.connect(
    lambda errors: warnings.extend(error.toString() for error in errors)
)
engine.addImportPath(str(root / "prismqml"))
register_types(engine)
component = QQmlComponent(engine)
component.setData(
    b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 120
    height: 130
    visible: true
    color: Enums.backgroundColor

    TimelineGraphLayer {
        width: 64
        height: 65
        graphData: ({"segments": [
            {"fromLane": 0, "toLane": 0, "colorIndex": 0}
        ]})
        showNode: false
        nodeY: 0
        selected: false
    }

    TimelineGraphLayer {
        y: 65
        width: 64
        height: 65
        graphData: ({"segments": [
            {"fromLane": 0, "toLane": 0, "colorIndex": 0}
        ]})
        showNode: false
        nodeY: 0
        selected: false
    }
}
""",
    QUrl.fromLocalFile(
        str(
            root
            / "prismqml"
            / "PrismQML"
            / "controls"
            / "containers"
            / "timeline-graph-boundary-probe.qml"
        )
    ),
)
assert component.status() == QQmlComponent.Status.Ready, [
    error.toString() for error in component.errors()
]
window = component.create(engine.rootContext())
assert window is not None, [error.toString() for error in component.errors()]
loop = QEventLoop()
QTimer.singleShot(400, loop.quit)
loop.exec()
image = window.grabWindow()
assert not image.isNull()
scale = image.width() / window.width()
sample_x = round(16 * scale)
boundary = round(65 * scale)
interior = image.pixelColor(sample_x, boundary - 4)
junction = [
    image.pixelColor(sample_x, sample_y)
    for sample_y in range(boundary - 1, boundary + 2)
]
assert all(color == interior for color in junction), (
    interior.name(),
    [color.name() for color in junction],
    scale,
)
assert warnings == [], warnings
print("TIMELINE_GRAPH_BOUNDARY_OK", interior.name(), scale)
window.close()
window.deleteLater()
component.deleteLater()
engine.deleteLater()
app.processEvents()
'''


def test_timeline_graph_stays_opaque_across_scaled_delegate_boundaries():
    """Scaled adjacent rows must not expose a one-pixel seam. 缩放后相邻行不得露出像素缝。"""
    environment = os.environ.copy()
    environment["QT_SCALE_FACTOR"] = "1.5"
    result = subprocess.run(
        [
            sys.executable,
            str(TEST_PROCESS),
            "--qt-platform",
            "offscreen",
            "--timeout",
            "60",
            "--",
            sys.executable,
            "-X",
            "utf8",
            "-c",
            BOUNDARY_PROBE,
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
    assert "TIMELINE_GRAPH_BOUNDARY_OK" in output
    if sys.platform == "win32":
        assert "visible_windows=0 / job_active_processes=0" in output
