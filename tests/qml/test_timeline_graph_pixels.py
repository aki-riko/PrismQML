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

from PySide6.QtCore import QEventLoop, QPointF, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem
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
    width: 420
    height: 420
    visible: true
    color: Enums.backgroundColor

    TimelineCore {
        objectName: "timeline"
        x: 20
        y: 20
        width: 380
        height: 380
        type: Enums.timeline.type_graph
        graphLaneCount: 2
        graphPalette: ["#0078d4", "#107c10"]
        items: [{
            "title": "Graph",
            "graph": {"segments": [
                {"fromLane": 0, "toLane": 0, "colorIndex": 0}
            ]},
            "cards": [
                {"text": "Branch", "graph": {"nodeLane": 0,
                    "nodeColorIndex": 0, "segments": [
                        {"fromLane": 0, "toLane": 0, "colorIndex": 0,
                            "endAtNode": true},
                        {"fromLane": 0, "toLane": 0, "colorIndex": 0,
                            "startAtNode": true},
                        {"fromLane": 0, "toLane": 1, "colorIndex": 1,
                            "startAtNode": true}
                    ]}},
                {"text": "Two", "graph": {"nodeLane": 0,
                    "nodeColorIndex": 0, "segments": [
                        {"fromLane": 0, "toLane": 0, "colorIndex": 0},
                        {"fromLane": 1, "toLane": 1, "colorIndex": 1}
                    ]}},
                {"text": "Three", "graph": {"nodeLane": 0,
                    "nodeColorIndex": 0, "segments": [
                        {"fromLane": 0, "toLane": 0, "colorIndex": 0},
                        {"fromLane": 1, "toLane": 1, "colorIndex": 1}
                    ]}},
                {"text": "Merge", "graph": {"nodeLane": 0,
                    "nodeColorIndex": 0, "segments": [
                        {"fromLane": 0, "toLane": 0, "colorIndex": 0,
                            "endAtNode": true},
                        {"fromLane": 1, "toLane": 0, "colorIndex": 1,
                            "endAtNode": true},
                        {"fromLane": 0, "toLane": 0, "colorIndex": 0,
                            "startAtNode": true}
                    ]}},
                {"text": "Five", "graph": {"nodeLane": 0,
                    "nodeColorIndex": 0, "segments": [
                        {"fromLane": 0, "toLane": 0, "colorIndex": 0}
                    ]}}
            ]
        }]
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
timeline = window.findChild(QQuickItem, "timeline")
assert timeline is not None
list_view = next(
    item
    for item in timeline.findChildren(QQuickItem)
    if "ListView" in item.metaObject().className()
)
list_view.setProperty("contentY", 23.25)
QTimer.singleShot(200, loop.quit)
loop.exec()
image = window.grabWindow()
assert not image.isNull()
scale = image.width() / window.width()

def visual_descendants(item):
    descendants = []
    for child in item.childItems():
        descendants.append(child)
        descendants.extend(visual_descendants(child))
    return descendants

layer_rows = sorted(
    (
        (item, item.parentItem())
        for item in visual_descendants(timeline)
        if item.objectName() == "timelineGraphLayer" and item.isVisible()
    ),
    key=lambda pair: pair[1].mapToScene(QPointF(0, 0)).y(),
)
assert len(layer_rows) >= 4, len(layer_rows)
boundaries = []
for current, following in zip(layer_rows, layer_rows[1:]):
    current_layer, current_row = current
    _following_layer, following_row = following
    current_bottom = current_row.mapToScene(QPointF(0, current_row.height())).y()
    following_top = following_row.mapToScene(QPointF(0, 0)).y()
    if abs(current_bottom - following_top) < 0.01:
        boundaries.append((current_layer, current_bottom))
assert len(boundaries) >= 3, boundaries

failures = []
for layer, boundary_y in boundaries:
    lane_x = layer.mapToScene(QPointF(16, 0)).x()
    sample_x = round(lane_x * scale)
    boundary = round(boundary_y * scale)
    profile_radius = 4

    def horizontal_profile(sample_y):
        return [
            image.pixelColor(sample_point, sample_y).rgba()
            for sample_point in range(
                sample_x - profile_radius, sample_x + profile_radius + 1
            )
        ]

    interior_profile = horizontal_profile(boundary - 6)
    junction_profiles = [
        horizontal_profile(sample_y)
        for sample_y in range(boundary - 1, boundary + 2)
    ]
    if any(profile != interior_profile for profile in junction_profiles):
        failures.append((boundary_y, interior_profile, junction_profiles))
assert failures == [], (failures, scale, list_view.property("contentY"))

branch_channel_tolerance = 2
branch_edge_chroma_threshold = 8
node_chroma_threshold = 40

def max_channel_delta(left, right):
    return max(
        abs(((left >> shift) & 0xff) - ((right >> shift) & 0xff))
        for shift in (0, 8, 16, 24)
    )

branch_failures = []
branch_boundaries = []
for current, following in zip(layer_rows, layer_rows[1:]):
    current_layer, current_row = current
    following_layer, following_row = following
    current_bottom = current_row.mapToScene(QPointF(0, current_row.height())).y()
    following_top = following_row.mapToScene(QPointF(0, 0)).y()
    if abs(current_bottom - following_top) >= 0.01:
        continue
    current_data = current_layer.property("graphData") or {}
    following_data = following_layer.property("graphData") or {}
    current_segments = current_data.get("segments", [])
    following_segments = following_data.get("segments", [])
    curve_before = any(
        segment.get("colorIndex") == 1
        and segment.get("fromLane") != segment.get("toLane")
        and not segment.get("endAtNode", False)
        for segment in current_segments
    )
    curve_after = any(
        segment.get("colorIndex") == 1
        and segment.get("fromLane") != segment.get("toLane")
        and not segment.get("startAtNode", False)
        for segment in following_segments
    )
    if not curve_before and not curve_after:
        continue
    branch_boundaries.append((current_layer, current_bottom, curve_before))

assert len(branch_boundaries) == 2, branch_boundaries
for layer, boundary_y, curve_before in branch_boundaries:
    lane_x = layer.mapToScene(QPointF(32, 0)).x()
    sample_x = round(lane_x * scale)
    boundary = round(boundary_y * scale)
    profile_radius = 4

    def branch_profile(sample_y):
        return [
            image.pixelColor(sample_point, sample_y).rgba()
            for sample_point in range(
                sample_x - profile_radius, sample_x + profile_radius + 1
            )
        ]

    interior_offset = 6 if curve_before else -6
    interior_profile = branch_profile(boundary + interior_offset)
    junction_profiles = [
        branch_profile(sample_y)
        for sample_y in range(boundary - 1, boundary + 2)
    ]

    def branch_stroke_mask(profile):
        return [
            ((color >> 8) & 0xff)
            - max((color >> 16) & 0xff, color & 0xff)
            > branch_edge_chroma_threshold
            for color in profile
        ]

    interior_mask = branch_stroke_mask(interior_profile)
    mismatched_profiles = [
        profile
        for profile in junction_profiles
        if branch_stroke_mask(profile) != interior_mask
        or any(
            max_channel_delta(color, interior_color) > branch_channel_tolerance
            for color, interior_color, is_stroke in zip(
                profile, interior_profile, branch_stroke_mask(profile)
            )
            if is_stroke
        )
    ]
    if mismatched_profiles:
        branch_failures.append(
            (boundary_y, curve_before, interior_profile, mismatched_profiles)
        )
assert branch_failures == [], (
    branch_failures,
    scale,
    list_view.property("contentY"),
)

node_failures = []

def is_graph_pixel(color):
    channels = ((color >> 16) & 0xff, (color >> 8) & 0xff, color & 0xff)
    return max(channels) - min(channels) > node_chroma_threshold

for layer, _row in layer_rows:
    if not layer.property("showNode"):
        continue
    lane_x = layer.mapToScene(QPointF(16, 0)).x()
    node_y = layer.mapToScene(
        QPointF(0, float(layer.property("nodeY")))
    ).y()
    sample_x = round(lane_x * scale)
    sample_y = round(node_y * scale)
    sample_span = round(9 * scale)
    profile = [
        image.pixelColor(sample_x, point_y).rgba()
        for point_y in range(sample_y - sample_span, sample_y + sample_span + 1)
    ]
    if any(not is_graph_pixel(color) for color in profile):
        node_failures.append((node_y, profile))
assert node_failures == [], (node_failures, scale, list_view.property("contentY"))
assert warnings == [], warnings
print(
    "TIMELINE_GRAPH_CONTINUITY_OK",
    len(boundaries),
    len(layer_rows) - 1,
    scale,
)
window.close()
window.deleteLater()
component.deleteLater()
engine.deleteLater()
app.processEvents()
'''


def test_timeline_graph_keeps_uniform_stroke_across_rows_and_nodes():
    """Scaled row joins and commit nodes must retain a continuous stroke. 缩放后接缝与提交点须连续。"""
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
    assert "TIMELINE_GRAPH_CONTINUITY_OK" in output
    if sys.platform == "win32":
        assert "visible_windows=0 / job_active_processes=0" in output
