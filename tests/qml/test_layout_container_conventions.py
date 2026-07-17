# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Container layout runtime contracts. 容器布局运行时合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPoint,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
LAYOUT_DIR = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "containers" / "Layout"
)
SOURCE_PATHS = [
    LAYOUT_DIR / name
    for name in (
        "GridLayout.qml",
        "HBoxLayout.qml",
        "RowFit.qml",
        "SplitPane.qml",
        "VBoxLayout.qml",
    )
]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "layout-container-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property var hboxGeometry: [
        hbox.contentWidth, hbox.contentHeight,
        hboxA.x, hboxA.y, hboxA.width, hboxA.height,
        hboxB.x, hboxB.y, hboxB.width, hboxB.height
    ]
    readonly property var vboxGeometry: [
        vbox.contentWidth, vbox.contentHeight,
        vboxA.x, vboxA.y, vboxA.width, vboxA.height,
        vboxB.x, vboxB.y, vboxB.width, vboxB.height
    ]
    readonly property var gridGeometry: [
        grid.contentWidth, grid.contentHeight,
        gridA.x, gridA.y, gridA.width, gridA.height,
        gridB.x, gridB.y, gridB.width, gridB.height
    ]
    readonly property var layoutCounts: [hbox.count(), vbox.count(), grid.count()]
    readonly property bool layoutItemsMatch:
        hbox.itemAt(1) === hboxB && hbox.indexOf(hboxA) === 0
        && vbox.itemAt(1) === vboxB && vbox.indexOf(vboxA) === 0
        && grid.itemAt(1) === gridB && grid.indexOf(gridA) === 0
    readonly property real rowFitScale: rowFit.children[0].scale
    readonly property real rowFitImplicitWidth: rowFit.implicitWidth
    readonly property var layoutMargins: [
        hbox.leftPadding, hbox.topPadding, hbox.rightPadding, hbox.bottomPadding,
        vbox.leftPadding, vbox.topPadding, vbox.rightPadding, vbox.bottomPadding,
        grid.leftPadding, grid.topPadding, grid.rightPadding, grid.bottomPadding
    ]
    readonly property var gridSpacings: [
        grid.horizontalSpacing, grid.verticalSpacing
    ]

    function configureLayouts() {
        hbox.setContentsMargins(1, 2, 3, 4)
        vbox.setContentsMargins(5, 6, 7, 8)
        grid.setContentsMargins(9, 10, 11, 12)
        grid.setSpacing(6)
    }

    function setVerticalSplit() {
        split.orientation = Qt.Vertical
        split.splitPosition = 0.25
    }

    width: 760
    height: 620
    visible: false

    HBoxLayout {
        id: hbox
        x: 10
        y: 10
        preferredWidth: 220
        preferredHeight: 60
        margins: 10
        spacing_: 8

        Rectangle { id: hboxA; width: 40; height: 20 }
        Rectangle { id: hboxB; width: 60; height: 30 }
    }

    VBoxLayout {
        id: vbox
        x: 250
        y: 10
        preferredWidth: 120
        preferredHeight: 120
        margins: 10
        spacing_: 8

        Rectangle { id: vboxA; width: 40; height: 20 }
        Rectangle { id: vboxB; width: 60; height: 30 }
    }

    GridLayout {
        id: grid
        x: 390
        y: 10
        preferredWidth: 220
        preferredHeight: 100
        margins: 10
        columns: 2
        horizontalSpacing: 8
        verticalSpacing: 6

        Rectangle { id: gridA; width: 40; height: 20 }
        Rectangle { id: gridB; width: 60; height: 30 }
    }

    RowFit {
        id: rowFit
        x: 10
        y: 180
        width: 100
        height: 40
        autoFit: true
        padding: 8
        spacing: 8

        Rectangle { id: rowFitProbe; width: 80; height: 20 }
        Rectangle { width: 40; height: 20 }
    }

    SplitPane {
        id: split
        objectName: "splitPane"
        x: 300
        y: 300
        width: 300
        height: 200
        handleWidth: 8
        minimumSize: 50

        firstContent: Item { id: firstPane; objectName: "firstContent" }
        secondContent: Item { id: secondPane; objectName: "secondContent" }
    }

}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is accepted for accepted in allowed)
    ]


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
    _pump()
    return engine, component, window, warnings


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
def layout_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene()
    try:
        yield window, warnings, windows_before
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_linear_and_grid_layout_geometry_and_api(layout_scene):
    window, warnings, windows_before = layout_scene
    assert _variant(window.property("layoutCounts")) == [2, 2, 2]
    assert window.property("layoutItemsMatch")
    assert _variant(window.property("hboxGeometry")) == pytest.approx(
        [128, 50, 0, 10, 40, 20, 85, 5, 60, 30]
    )
    assert _variant(window.property("vboxGeometry")) == pytest.approx(
        [80, 78, 0, 9, 40, 20, 0, 58, 60, 30]
    )
    assert _variant(window.property("gridGeometry")) == pytest.approx(
        [128, 50, 0, 30, 40, 20, 85, 25, 60, 30]
    )
    assert QMetaObject.invokeMethod(window, "configureLayouts")
    assert _variant(window.property("layoutMargins")) == list(range(1, 13))
    assert _variant(window.property("gridSpacings")) == [6, 6]
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_row_fit_scale_and_split_pane_geometry(layout_scene):
    window, warnings, windows_before = layout_scene
    assert window.property("rowFitImplicitWidth") == pytest.approx(144)
    assert window.property("rowFitScale") == pytest.approx(84 / 128)
    split = window.findChild(QQuickItem, "splitPane")
    first = split.findChild(QQuickItem, "firstPane")
    second = split.findChild(QQuickItem, "secondPane")
    handle = next(
        item
        for item in split.findChildren(QQuickItem)
        if item.metaObject().className().startswith("QQuickRectangle")
        and item.width() == pytest.approx(8)
        and item.height() == pytest.approx(200)
    )
    assert (first.width(), first.height()) == pytest.approx((146, 200))
    assert (handle.x(), handle.y(), handle.width(), handle.height()) == pytest.approx(
        (146, 0, 8, 200)
    )
    assert (second.width(), second.height()) == pytest.approx((146, 200))
    assert QMetaObject.invokeMethod(window, "setVerticalSplit")
    _pump()
    assert (first.width(), first.height()) == pytest.approx((300, 48))
    assert (handle.x(), handle.y(), handle.width(), handle.height()) == pytest.approx(
        (0, 48, 300, 8)
    )
    assert (second.width(), second.height()) == pytest.approx((300, 144))
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_split_pane_real_drag_clamps_minimum(layout_scene):
    window, warnings, windows_before = layout_scene
    window.show()
    _pump()
    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=QPoint(450, 400))
    QTest.mouseMove(window, QPoint(320, 400), delay=10)
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=QPoint(320, 400))
    _pump()
    split = window.findChild(QQuickItem, "splitPane")
    assert split.property("splitPosition") == pytest.approx(50 / 292)
    window.hide()
    _pump()
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_container_layout_sources_follow_conventions():
    for source_path in SOURCE_PATHS:
        source = source_path.read_text(encoding="utf-8")
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations = scan_source_text(source, path)
        assert [
            violation
            for violation in violations
            if violation.rule in {"QML008", "QML009"}
        ] == []
