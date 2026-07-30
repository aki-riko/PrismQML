# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Waterfall and Separator runtime contracts. Waterfall 与 Separator 运行时合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATHS = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "containers" / "Waterfall.qml",
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "Separator"
    / "Separator.qml",
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "container-leaf-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property real waterfallHeight: waterfall.contentHeight

    width: 640
    height: 360
    visible: true

    Component {
        id: waterfallDelegate
        Rectangle {
            width: parent ? parent.width : 0
            height: modelData
        }
    }

    Waterfall {
        id: waterfall
        objectName: "waterfall"
        x: 20
        y: 20
        width: 220
        columns: 2
        spacing: 10
        model: [50, 80, 40, 70]
        delegate: waterfallDelegate
    }

    Separator {
        id: horizontal
        objectName: "horizontalSeparator"
        x: 300
        y: 20
        type: 0
        lineWidth: 2
        lineLength: 160
    }

    Separator {
        id: vertical
        objectName: "verticalSeparator"
        x: 300
        y: 60
        type: 1
        lineWidth: 3
        lineLength: 120
    }

    Separator {
        id: autoHorizontal
        objectName: "autoHorizontalSeparator"
        x: 340
        y: 20
        type: 0
        lineLength: 0
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1000) -> bool:
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


def _visual_items(item):
    result = []
    for child in item.childItems():
        result.append(child)
        result.extend(_visual_items(child))
    return result


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
    items = {
        name: window.findChild(QQuickItem, name)
        for name in (
            "waterfall",
            "horizontalSeparator",
            "verticalSeparator",
            "autoHorizontalSeparator",
        )
    }
    assert all(items.values())
    _pump()
    return engine, component, window, items, warnings


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
def leaf_scene(qapp):
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    try:
        yield (*scene[2:], windows_before)
    finally:
        _dispose_scene(scene[0], scene[1], scene[2])
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_waterfall_places_items_in_shortest_columns(leaf_scene):
    window, items, warnings, windows_before = leaf_scene
    waterfall = items["waterfall"]
    assert _wait_for(
        lambda: len(
            [
                item
                for item in _visual_items(waterfall)
                if item.property("itemIndex") is not None
            ]
        )
        == 4
    )
    loaders = sorted(
        (
            item
            for item in _visual_items(waterfall)
            if item.property("itemIndex") is not None
        ),
        key=lambda item: item.property("itemIndex"),
    )
    assert [loader.width() for loader in loaders] == pytest.approx([105] * 4)
    assert [loader.x() for loader in loaders] == pytest.approx([0, 115, 0, 115]), (
        [loader.property("targetColumn") for loader in loaders],
        [loader.y() for loader in loaders],
        waterfall.property("columnHeights"),
        window.property("waterfallHeight"),
    )
    assert [loader.y() for loader in loaders] == pytest.approx([0, 0, 60, 90])
    assert window.property("waterfallHeight") == pytest.approx(170)

    waterfall.setWidth(320)
    assert _wait_for(lambda: loaders[0].width() == pytest.approx(155))
    assert [loader.x() for loader in loaders] == pytest.approx([0, 165, 0, 165])
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_waterfall_zero_columns_use_one_finite_column(leaf_scene):
    window, items, warnings, windows_before = leaf_scene
    waterfall = items["waterfall"]
    waterfall.setProperty("columns", 0)
    waterfall.setProperty("model", [52])
    assert _wait_for(lambda: waterfall.property("_safeColumns") == 1)
    assert _wait_for(
        lambda: waterfall.property("contentHeight") == pytest.approx(62)
    )
    loaders = [
        item
        for item in _visual_items(waterfall)
        if item.property("itemIndex") is not None
    ]
    assert len(loaders) == 1
    assert loaders[0].x() == pytest.approx(0)
    assert loaders[0].width() == pytest.approx(220)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_waterfall_coalesces_bulk_loader_relayout(leaf_scene):
    window, items, warnings, windows_before = leaf_scene
    waterfall = items["waterfall"]
    relayouts_before = waterfall.property("_relayoutCount")

    waterfall.setProperty("model", [40 + index % 5 * 10 for index in range(100)])
    assert _wait_for(
        lambda: len(
            [
                item
                for item in _visual_items(waterfall)
                if item.property("itemIndex") is not None
            ]
        )
        == 100
    )
    assert _wait_for(lambda: waterfall.property("_relayoutCount") > relayouts_before)
    _pump(100)

    assert waterfall.property("_relayoutCount") - relayouts_before <= 3
    assert waterfall.property("contentHeight") > 0
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_separator_fixed_and_auto_geometry(leaf_scene):
    window, items, warnings, windows_before = leaf_scene
    horizontal = items["horizontalSeparator"]
    vertical = items["verticalSeparator"]
    auto_horizontal = items["autoHorizontalSeparator"]
    assert horizontal.width() == pytest.approx(160)
    assert horizontal.height() == pytest.approx(2)
    assert vertical.width() == pytest.approx(3)
    assert vertical.height() == pytest.approx(120)
    assert auto_horizontal.width() == pytest.approx(100)
    assert auto_horizontal.height() == pytest.approx(1)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_container_leaf_sources_follow_conventions():
    violations = []
    for source_path in SOURCE_PATHS:
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations.extend(
            violation
            for violation in scan_source_text(
                source_path.read_text(encoding="utf-8"), path
            )
            if violation.rule in {"QML008", "QML009"}
        )
    assert violations == []
