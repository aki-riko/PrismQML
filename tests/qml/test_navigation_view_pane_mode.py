# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""NavigationView pane display mode contracts. 导航面板显示模式契约。"""

import time
from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import configure_qml_environment, register_types


SCENE_URL = QUrl.fromLocalFile(
    str(Path(__file__).resolve().parent / "navigation-view-pane-mode.qml")
)

MODEL = """
        model: [
            { key: "home", text: "Home" },
            { key: "docs", text: "Documents" }
        ]
"""

SCENE = f"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {{
    id: root
    objectName: "window"

    readonly property int systemUnspecified: Enums.navigation.pane_unspecified
    readonly property int systemAuto: Enums.navigation.pane_auto
    readonly property int systemLeft: Enums.navigation.pane_left
    readonly property int systemCompact: Enums.navigation.pane_left_compact
    readonly property int systemMinimal: Enums.navigation.pane_left_minimal
    readonly property int expandWidth: Enums.controlSize.navPanelExpandWidth

    width: 900
    height: 460
    visible: true

    function widenAutoPane() {{ autoPane.width = root.expandWidth }}
    function openMinimalPane() {{ minimalPane.openPane() }}
    function closeMinimalPane() {{ minimalPane.closePane() }}

    NavigationView {{
        id: legacyPane
        objectName: "legacyPane"
        x: 0
        width: 200
        height: 440
        showReturnButton: false
        titleBarHeight: 0
        isExpanded: true
{MODEL}    }}
    NavigationView {{
        id: leftPane
        objectName: "leftPane"
        x: 210
        width: 200
        height: 440
        showReturnButton: false
        titleBarHeight: 0
        paneDisplayMode: Enums.navigation.pane_left
{MODEL}    }}
    NavigationView {{
        id: compactPane
        objectName: "compactPane"
        x: 420
        width: 48
        height: 440
        showReturnButton: false
        titleBarHeight: 0
        paneDisplayMode: Enums.navigation.pane_left_compact
{MODEL}    }}
    NavigationView {{
        id: autoPane
        objectName: "autoPane"
        x: 480
        width: 48
        height: 440
        showReturnButton: false
        titleBarHeight: 0
        paneDisplayMode: Enums.navigation.pane_auto
{MODEL}    }}
    NavigationView {{
        id: minimalPane
        objectName: "minimalPane"
        x: 540
        width: 48
        height: 440
        showReturnButton: false
        titleBarHeight: 0
        paneDisplayMode: Enums.navigation.pane_left_minimal
{MODEL}    }}
}}
"""


def _pump(milliseconds: int = 12) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump(10)
        elapsed += 10
    return predicate()


def _create_scene(qapp):
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE.encode("utf-8"), SCENE_URL)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    _pump(150)
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(20)


def _pane(window: QQuickWindow, name: str):
    pane = window.findChild(QQuickItem, name)
    assert pane is not None, f"pane {name} not found"
    return pane


def _items_flickable(pane):
    """The pane's item viewport, found through the visual tree.

    通过视觉树定位面板的条目视口。
    """
    pending = list(pane.childItems())
    while pending:
        item = pending.pop(0)
        pending.extend(item.childItems())
        if item.inherits("QQuickFlickable"):
            return item
    raise AssertionError("pane item viewport not found")


def test_unspecified_mode_keeps_is_expanded_caller_owned(qapp):
    """Without a mode the pane must not touch isExpanded.

    未指定模式时面板不得改动 isExpanded。
    """
    engine, component, window, warnings = _create_scene(qapp)
    try:
        legacy = _pane(window, "legacyPane")
        assert legacy.property("paneDisplayMode") == window.property(
            "systemUnspecified"
        )
        assert legacy.property("isExpanded") is True
        # Changing the width must not flip it either 改宽度也不得翻转
        legacy.setProperty("width", 480)
        _pump(80)
        assert legacy.property("isExpanded") is True
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_left_and_compact_modes_drive_is_expanded(qapp):
    """Explicit modes own isExpanded regardless of the pane width.

    显式模式接管 isExpanded, 与面板宽度无关。
    """
    engine, component, window, warnings = _create_scene(qapp)
    try:
        left = _pane(window, "leftPane")
        compact = _pane(window, "compactPane")
        assert left.property("effectivePaneDisplayMode") == window.property(
            "systemLeft"
        )
        assert left.property("isExpanded") is True
        assert compact.property("effectivePaneDisplayMode") == window.property(
            "systemCompact"
        )
        assert compact.property("isExpanded") is False
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_auto_mode_follows_its_own_width(qapp):
    """Auto expands once the pane can hold the expanded design width.

    自动模式在面板装得下展开设计宽度时展开。
    """
    engine, component, window, warnings = _create_scene(qapp)
    try:
        auto = _pane(window, "autoPane")
        assert auto.property("effectivePaneDisplayMode") == window.property(
            "systemCompact"
        )
        assert auto.property("isExpanded") is False

        window.widenAutoPane()
        assert _wait_for(
            lambda: auto.property("effectivePaneDisplayMode")
            == window.property("systemLeft")
        ), "auto did not switch to left when widened"
        assert _wait_for(lambda: auto.property("isExpanded") is True)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_minimal_mode_hides_items_until_the_pane_is_opened(qapp):
    """Minimal keeps only the menu button while closed.

    极简模式折叠时只保留菜单按钮。
    """
    engine, component, window, warnings = _create_scene(qapp)
    try:
        minimal = _pane(window, "minimalPane")
        assert minimal.property("effectivePaneDisplayMode") == window.property(
            "systemMinimal"
        )
        assert minimal.property("isPaneOpen") is False
        assert minimal.property("isExpanded") is False
        assert minimal.property("itemsVisible") is False
        viewport = _items_flickable(minimal)
        assert viewport.property("visible") is False

        window.openMinimalPane()
        assert _wait_for(lambda: minimal.property("isPaneOpen") is True)
        assert _wait_for(lambda: minimal.property("isExpanded") is True)
        assert minimal.property("itemsVisible") is True
        assert viewport.property("visible") is True

        window.closeMinimalPane()
        assert _wait_for(lambda: minimal.property("isPaneOpen") is False)
        assert _wait_for(lambda: minimal.property("itemsVisible") is False)
        assert viewport.property("visible") is False
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
