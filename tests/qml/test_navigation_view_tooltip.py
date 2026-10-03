# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""NavigationView compact item tooltip contracts. NavigationView 紧凑项工具提示合同。"""

from pathlib import Path
from pathlib import PurePosixPath

import pytest

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPoint,
    QPointF,
    QObject,
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
NAVIGATION_VIEW_SOURCE = (
    ROOT / "prismqml" / "PrismQML" / "navigation" / "NavigationView.qml"
)
NAVIGATION_ITEM_SOURCE = (
    ROOT / "prismqml" / "PrismQML" / "navigation" / "NavigationViewItem.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "navigation-view-tooltip.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: host
    objectName: "host"
    readonly property real tooltipGap: Enums.spacing.xs
    readonly property color hoverColor: Enums.stateColor.hover
    width: 640
    height: 260
    visible: true

    NavigationView {
        id: view
        objectName: "navigationView"
        width: 64
        height: parent.height
        titleBarHeight: 0
        showReturnButton: false
        isExpanded: false
        showCompactItemToolTips: true
        compactItemToolTipShowDelay: 0
        model: [
            { key: "home", text: "Home", icon: "H" },
            { key: "settings", text: "Settings", icon: "S" }
        ]
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_until(predicate, timeout_ms: int = 2000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _descendants(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _descendants(child)


def _navigation_item(view: QQuickItem, text: str) -> QQuickItem:
    return next(
        item
        for item in _descendants(view)
        if "NavigationViewItem" in item.metaObject().className()
        and item.property("text") == text
    )


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
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    _pump(100)
    return engine, component, window, warnings


def _dispose_scene(engine, component, window):
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture
def navigation_tooltip_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene()
    try:
        yield window, warnings, windows_before
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_navigation_view_compact_item_tooltip_is_right_aligned_and_clickable(
    navigation_tooltip_scene,
):
    window, warnings, windows_before = navigation_tooltip_scene
    view = window.findChild(QQuickItem, "navigationView")
    item = _navigation_item(view, "Settings")
    assert view.property("isCompact") is True
    assert item.property("toolTipText") == "Settings"

    clicked = []
    view.itemClicked.connect(clicked.append)
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
    QTest.mouseMove(window, point)
    assert _wait_until(lambda: item.property("hovered") is True)
    assert item.property("pressed") is False

    def visible_tooltip():
        tooltip = item.findChild(QObject, "_toolTip")
        return tooltip if tooltip is not None and tooltip.property("visible") else None

    assert _wait_until(visible_tooltip)
    tooltip = visible_tooltip()
    assert tooltip is not None
    assert item.property("hovered") is True
    content_item = tooltip.property("contentItem")
    assert content_item.property("text") == "Settings"
    assert item.property("_touchActive") is True
    assert item.property("_navItemBackground") == window.property("hoverColor")
    assert tooltip.property("x") >= item.width() + window.property("tooltipGap") - 0.5

    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=point)
    assert _wait_until(lambda: clicked == [1])
    assert warnings == []
    QTest.mouseMove(window, QPoint(window.width() - 1, window.height() - 1))
    assert _wait_until(lambda: not tooltip.property("visible"))
    assert item.property("_toolTipHovered") is False
    assert _wait_until(lambda: item.property("hovered") is False)
    assert [
        candidate
        for candidate in QGuiApplication.topLevelWindows()
        if candidate.isVisible()
        and candidate not in windows_before
        and candidate is not window
    ] == []


def test_navigation_view_compact_item_tooltip_is_disabled_when_expanded(
    navigation_tooltip_scene,
):
    window, warnings, _windows_before = navigation_tooltip_scene
    view = window.findChild(QQuickItem, "navigationView")
    item = _navigation_item(view, "Home")

    view.setProperty("isExpanded", True)
    _pump()
    assert view.property("isCompact") is False
    assert item.property("toolTipText") == ""
    view.setProperty("showCompactItemToolTips", False)
    view.setProperty("isExpanded", False)
    _pump()
    assert item.property("toolTipText") == ""
    assert warnings == []


def test_navigation_view_tooltip_sources_follow_qml_conventions():
    navigation_view_source = NAVIGATION_VIEW_SOURCE.read_text(encoding="utf-8")
    navigation_item_source = NAVIGATION_ITEM_SOURCE.read_text(encoding="utf-8")
    navigation_view_path = PurePosixPath(
        NAVIGATION_VIEW_SOURCE.relative_to(ROOT).as_posix()
    )
    navigation_item_path = PurePosixPath(
        NAVIGATION_ITEM_SOURCE.relative_to(ROOT).as_posix()
    )
    violations = scan_source_text(navigation_view_source, navigation_view_path)
    violations.extend(scan_source_text(navigation_item_source, navigation_item_path))
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009", "QML011"}
    ] == []
    assert "property bool showCompactItemToolTips: true" in navigation_view_source
    assert (
        "toolTipText: control.showCompactItemToolTips && control.isCompact"
        in navigation_view_source
    )
    assert "toolTipPosition: Enums.position.right" in navigation_view_source
    assert (
        'source: "../controls/containers/_internal/WidgetToolTipSupport.qml"'
        in navigation_item_source
    )
