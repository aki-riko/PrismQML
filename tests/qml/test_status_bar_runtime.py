# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""StatusBar structured state contracts. StatusBar 结构化状态合同。"""

from pathlib import Path, PurePosixPath
import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QPointF, QTimer, QUrl, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
STATUS_BAR_SOURCE = ROOT / "prismqml" / "PrismQML" / "navigation" / "StatusBar.qml"
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "status-bar-runtime.qml"))
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    property int clickCount: 0
    property string lastSide: ""
    property string lastText: ""

    width: 480
    height: 80
    visible: true

    StatusBar {
        id: statusBar
        objectName: "statusBar"
        anchors.fill: parent
        message: "Ready"
        accessibleName: "Editor status"
        level: Enums.statusLevel.success
        progress: 0.75
        leftItems: [
            "Line 12",
            {
                "text": "UTF-8",
                "icon": Enums.icon.document,
                "level": Enums.statusLevel.info,
                "tooltip": "File encoding",
                "clickable": true
            },
            {"text": "Hidden", "visible": false}
        ]
        rightItems: [
            {"text": "main", "tooltip": "Git branch", "clickable": true},
            {"text": "Disabled", "clickable": true, "enabled": false}
        ]
        onItemClicked: function(index, item, side) {
            root.clickCount += 1
            root.lastSide = side
            root.lastText = item.text || item
        }
    }

}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _item(root: QQuickItem, name: str) -> QQuickItem:
    item = root.findChild(QQuickItem, name)
    assert item is not None, name
    return item


def _click(window: QQuickWindow, item: QQuickItem) -> None:
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
    QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point)
    _pump(50)


def _create_scene() -> tuple[QQmlApplicationEngine, QQmlComponent, QQuickWindow]:
    engine = QQmlApplicationEngine()
    warnings: list[str] = []
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
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.show()
    _pump(100)
    assert warnings == [], warnings
    return engine, component, window


def _dispose_scene(
    engine: QQmlApplicationEngine, component: QQmlComponent, window: QQuickWindow
) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_status_bar_structured_items_progress_and_clicks(qapp):
    """结构化条目、进度边界与点击信号必须使用同一真实 QML 场景。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window = _create_scene()
    root = window
    try:
        status_bar = _item(root, "statusBar")
        progress = _item(root, "statusBarProgress")
        left_text = _item(root, "statusBarItem_left_0")
        encoding = _item(root, "statusBarItem_left_1")
        hidden = _item(root, "statusBarItem_left_2")
        branch = _item(root, "statusBarItem_right_0")
        disabled = _item(root, "statusBarItem_right_1")

        assert status_bar.property("message") == "Ready"
        assert progress.property("value") == pytest.approx(0.75)
        assert progress.property("indeterminate") is False
        assert hidden.isVisible() is False
        assert encoding.property("itemText") == "UTF-8"
        assert encoding.property("itemIcon") == "Document"
        assert encoding.property("toolTipText") == "File encoding"
        assert encoding.property("itemClickable") is True
        assert branch.property("itemClickable") is True
        assert disabled.property("itemClickable") is False
        assert left_text.property("itemText") == "Line 12"

        _click(window, branch)
        assert root.property("clickCount") == 1
        assert root.property("lastSide") == "right"
        assert root.property("lastText") == "main"

        _click(window, disabled)
        assert root.property("clickCount") == 1

        status_bar.setProperty("busy", True)
        assert progress.property("indeterminate") is True
        status_bar.setProperty("busy", False)
        status_bar.setProperty("progress", -0.5)
        assert progress.property("visible") is False
        status_bar.setProperty("progress", 1.5)
        assert progress.property("value") == pytest.approx(1.0)
        assert progress.property("visible") is True

        window.setWidth(220)
        _pump()
        left_end = encoding.mapToItem(status_bar, encoding.width(), 0).x()
        right_start = branch.mapToItem(status_bar, 0, 0).x()
        assert left_end <= right_start or encoding.width() == 0
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_status_bar_source_follows_conventions():
    violations = scan_source_text(
        STATUS_BAR_SOURCE.read_text(encoding="utf-8"),
        PurePosixPath(STATUS_BAR_SOURCE.relative_to(ROOT).as_posix()),
    )
    assert [
        violation for violation in violations if violation.rule in {"QML008", "QML009"}
    ] == []
