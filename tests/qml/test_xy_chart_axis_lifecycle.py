# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""XY chart axis branch lifecycle regressions. XY 图表坐标轴分支生命周期回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QPointF, QTimer, QUrl
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "xy-chart-axis-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/data/Chart/_internal" as ChartInternal

Window {
    id: root
    width: 640
    height: 360
    visible: true
    color: Enums.backgroundColor

    property int axisMode: 0
    property bool coreVisible: true
    property bool gridEnabled: true
    readonly property int verticalMode: 0
    readonly property int horizontalMode: 1
    readonly property int scatterMode: 2
    readonly property int captionType: Enums.label.type_caption
    readonly property color gridLineColor: Enums.chartColors.gridLine
    readonly property var samplePoints: [
        {"label": "A", "value": 1},
        {"label": "B", "value": 3},
        {"label": "C", "value": 2}
    ]
    readonly property var sampleSeries: [{
        "name": "Series",
        "data": [[1, 1], [2, 3], [3, 2]]
    }]

    ChartInternal.XYChartCore {
        objectName: "axisCore"
        anchors.fill: parent
        visible: root.coreVisible
        chartData: root.axisMode === root.scatterMode ? [] : root.samplePoints
        maxValue: 3
        showLabels: true
        showValues: true
        showGrid: root.gridEnabled
        title: ""
        series: root.axisMode === root.scatterMode ? root.sampleSeries : []
        isScatter: root.axisMode === root.scatterMode
        isHorizontal: root.axisMode === root.horizontalMode
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1500) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is accepted for accepted in allowed)
    ]


def _visual_descendants(item):
    descendants = []
    for child in item.childItems():
        descendants.append(child)
        descendants.extend(_visual_descendants(child))
    return descendants


def _has_ancestor_type(item, type_name: str) -> bool:
    parent = item.parentItem()
    while parent is not None:
        class_name = parent.metaObject().className().split("_QMLTYPE_")[0]
        if class_name == type_name:
            return True
        parent = parent.parentItem()
    return False


def _axis_labels(window, axis_core):
    caption_type = window.property("captionType")
    return [
        item
        for item in _visual_descendants(axis_core)
        if item.metaObject().indexOfProperty("type") >= 0
        and item.property("type") == caption_type
        and not _has_ancestor_type(item, "ChartTitle")
    ]


def _category_axis_labels(window, axis_core):
    return [
        label
        for label in _axis_labels(window, axis_core)
        if any(
            "MouseArea" in child.metaObject().className()
            for child in label.childItems()
        )
    ]


def _grid_lines(window, axis_core):
    grid_color = window.property("gridLineColor")
    return [
        item
        for item in _visual_descendants(axis_core)
        if "Rectangle" in item.metaObject().className()
        and item.metaObject().indexOfProperty("color") >= 0
        and item.property("color") == grid_color
    ]


def _stable_window_image(window) -> QImage:
    previous = QImage()
    stable_frames = 0
    for _ in range(40):
        current = window.grabWindow()
        assert not current.isNull()
        if current == previous:
            stable_frames += 1
            if stable_frames == 3:
                return current
        else:
            stable_frames = 0
        previous = current
        _pump()
    raise AssertionError("XYChartCore frame did not stabilize within 1.2 seconds")


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    axis_core = window.findChild(QQuickItem, "axisCore")
    assert axis_core is not None
    assert _wait_for(
        lambda: axis_core.width() == pytest.approx(window.width())
        and axis_core.height() == pytest.approx(window.height())
        and len(_axis_labels(window, axis_core)) == 8
    )
    return engine, component, window, axis_core, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture
def xy_axis_scene(qapp):
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    try:
        yield (*scene[2:], windows_before)
    finally:
        _dispose_scene(scene[0], scene[1], scene[2])
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


@pytest.mark.parametrize(
    ("mode_property", "expected_label_count", "expected_visible_count"),
    [
        ("verticalMode", 8, 8),
        ("horizontalMode", 8, 8),
        ("scatterMode", 11, 11),
    ],
)
def test_xy_axes_construct_only_active_direction_and_type_delegates(
    mode_property,
    expected_label_count,
    expected_visible_count,
    xy_axis_scene,
):
    window, axis_core, warnings, windows_before = xy_axis_scene
    assert window.setProperty("axisMode", window.property(mode_property))
    assert _wait_for(
        lambda: len(_axis_labels(window, axis_core)) == expected_label_count
    )
    labels = _axis_labels(window, axis_core)

    assert sum(label.isVisible() for label in labels) == expected_visible_count
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_xy_axes_skip_hidden_core_and_grid_delegates(
    xy_axis_scene,
):
    window, axis_core, warnings, windows_before = xy_axis_scene
    assert len(_grid_lines(window, axis_core)) == 5

    assert window.setProperty("gridEnabled", False)
    assert _wait_for(lambda: _grid_lines(window, axis_core) == [])

    assert window.setProperty("coreVisible", False)
    assert _wait_for(lambda: _axis_labels(window, axis_core) == [])
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_xy_axis_direction_pixel_roundtrip_and_first_hover(
    xy_axis_scene,
):
    window, axis_core, warnings, windows_before = xy_axis_scene
    hovered = []
    axis_core.xLabelHovered.connect(lambda index: hovered.append(index))
    vertical_image = _stable_window_image(window)
    visible_categories = [
        label
        for label in _category_axis_labels(window, axis_core)
        if label.isVisible()
    ]
    assert len(visible_categories) == 3
    first_label = min(
        visible_categories,
        key=lambda label: label.mapToScene(QPointF(0, 0)).x(),
    )
    hover_point = first_label.mapToScene(
        QPointF(first_label.width() / 2, first_label.height() / 2)
    ).toPoint()
    QTest.mouseMove(window, hover_point)
    assert _wait_for(lambda: hovered and hovered[-1] == 0)

    assert window.setProperty("axisMode", window.property("horizontalMode"))
    assert _wait_for(
        lambda: sum(
            label.isVisible() for label in _axis_labels(window, axis_core)
        )
        == 8
    )
    assert _stable_window_image(window) != vertical_image

    assert window.setProperty("axisMode", window.property("verticalMode"))
    assert _wait_for(
        lambda: sum(
            label.isVisible() for label in _axis_labels(window, axis_core)
        )
        == 8
    )
    assert _stable_window_image(window) == vertical_image
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []
