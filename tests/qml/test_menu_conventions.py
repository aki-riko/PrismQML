# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Menu component group runtime contracts. Menu 组件组运行时合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QMetaObject, QPoint, QPointF, QTimer, QUrl, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
MENU_SOURCE_PATHS = tuple(
    ROOT / "prismqml" / "PrismQML" / "controls" / "menus" / name
    for name in (
        "ContextMenu.qml",
        "MenuCore.qml",
        "MenuDelegate.qml",
        "SystemTrayMenu.qml",
        "TreeMenuDelegate.qml",
    )
)
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "menu-conventions.qml"))
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    property var openAction: null
    readonly property string openText: openAction ? openAction.text : ""
    readonly property bool openChecked: openAction ? openAction.checked : false
    readonly property bool contextBound: contextMenu._mouseArea !== null
    readonly property bool contextVisible: contextMenu.isVisible()
    readonly property bool trayAtCursor: trayMenu.showAtCursor

    function buildMenu() {
        openAction = menu.addAction("Open", "", "Ctrl+O", {
            "actionId": "open",
            "checkable": true,
            "checked": false,
            "toolTip": "Open item"
        })
        menu.addSeparator()
        menu.addActions([
            { "text": "Save", "actionId": "save" },
            { "text": "Disabled", "actionId": "disabled", "enabled": false }
        ])
    }
    function updateOpen() {
        menu.updateAction("open", { "text": "Open now", "checked": true })
    }
    function triggerOpen() { openAction.triggered() }
    function removeSave() { return menu.removeAction("save") }
    function clearMenu() { menu.clear() }
    function rebindContext() { contextMenu.bindToParent() }
    function showContext() { contextMenu.show(contextTarget) }
    function hideContext() { contextMenu.hide() }

    width: 720
    height: 360
    visible: true

    Rectangle {
        id: contextTarget
        objectName: "contextTarget"
        x: 20
        y: 20
        width: 160
        height: 80

        ContextMenu {
            id: contextMenu
            objectName: "contextMenu"
        }
    }

    MenuCore {
        id: menu
        objectName: "menuCore"
    }

    SystemTrayMenu {
        id: trayMenu
        objectName: "systemTrayMenu"
    }

    MenuDelegate {
        id: menuDelegate
        objectName: "menuDelegate"
        x: 240
        y: 20
        width: 240
        text: "Menu item"
        selected: true
    }

    TreeMenuDelegate {
        id: treeDelegate
        objectName: "treeMenuDelegate"
        x: 240
        y: 80
        width: 260
        text: "Tree item"
        hasChildren: true
        checkable: true
    }

    TreeMenuDelegate {
        id: treeLeafDelegate
        objectName: "treeLeafMenuDelegate"
        x: 240
        y: 140
        width: 260
        text: "Tree leaf item"
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1200) -> bool:
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


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [error.toString() for error in component.errors()]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    items = {
        name: window.findChild(QQuickItem, name)
        for name in (
            "menuCore",
            "contextMenu",
            "systemTrayMenu",
            "menuDelegate",
            "treeMenuDelegate",
            "treeLeafMenuDelegate",
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
def menu_scene(qapp):
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    try:
        yield (*scene[2:], windows_before)
    finally:
        _dispose_scene(scene[0], scene[1], scene[2])
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_menu_core_imperative_action_lifecycle(menu_scene):
    window, items, warnings, windows_before = menu_scene
    menu = items["menuCore"]
    triggered = []
    menu.actionTriggered.connect(triggered.append)
    assert QMetaObject.invokeMethod(window, "buildMenu")
    assert _wait_for(lambda: window.property("openText") == "Open")
    assert menu.getAction("open") is not None
    assert menu.getAction("save") is not None
    assert not menu.getAction("disabled").isEnabled()
    assert QMetaObject.invokeMethod(window, "updateOpen")
    assert window.property("openText") == "Open now"
    assert window.property("openChecked")
    assert QMetaObject.invokeMethod(window, "triggerOpen")
    assert _wait_for(lambda: triggered == ["open"])
    assert QMetaObject.invokeMethod(window, "removeSave")
    _pump()
    assert menu.getAction("save") is None
    assert QMetaObject.invokeMethod(window, "clearMenu")
    _pump()
    assert menu.getAction("open") is None
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_menu_delegates_and_context_binding(menu_scene):
    window, items, warnings, windows_before = menu_scene
    menu_delegate = items["menuDelegate"]
    tree_delegate = items["treeMenuDelegate"]
    tree_leaf_delegate = items["treeLeafMenuDelegate"]
    menu_clicks = []
    tree_expands = []
    tree_checks = []
    tree_leaf_clicks = []
    menu_delegate.clicked.connect(lambda: menu_clicks.append(True))
    tree_delegate.toggleExpand.connect(lambda: tree_expands.append(True))
    tree_delegate.checkToggled.connect(lambda: tree_checks.append(True))
    tree_leaf_delegate.clicked.connect(lambda: tree_leaf_clicks.append(True))

    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=QPoint(300, 36))
    assert _wait_for(lambda: menu_clicks == [True])
    mouse_areas = [
        child
        for child in tree_delegate.childItems()
        if "MouseArea" in child.metaObject().className() and child.isVisible()
    ]
    assert len(mouse_areas) == 2
    main_area = max(mouse_areas, key=lambda item: item.width())
    expand_area = min(mouse_areas, key=lambda item: item.width())
    main_pos = main_area.mapToScene(QPointF(main_area.width() / 2, main_area.height() / 2)).toPoint()
    expand_pos = expand_area.mapToScene(QPointF(expand_area.width() / 2, expand_area.height() / 2)).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=main_pos)
    assert _wait_for(lambda: tree_checks == [True])
    assert tree_expands == []
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=expand_pos)
    assert _wait_for(lambda: tree_expands == [True])
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=QPoint(300, 156))
    assert _wait_for(lambda: tree_leaf_clicks == [True])

    assert window.property("contextBound")
    assert not window.property("contextVisible")
    assert window.property("trayAtCursor")
    assert QMetaObject.invokeMethod(window, "rebindContext")
    assert window.property("contextBound")
    assert QMetaObject.invokeMethod(window, "showContext")
    assert _wait_for(lambda: window.property("contextVisible"))
    assert len(_new_visible_windows(windows_before, window)) == 1
    assert QMetaObject.invokeMethod(window, "hideContext")
    assert _wait_for(lambda: not window.property("contextVisible"))
    assert _wait_for(lambda: _new_visible_windows(windows_before, window) == [])
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_menu_sources_follow_conventions():
    violations = []
    for source_path in MENU_SOURCE_PATHS:
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations.extend(
            violation
            for violation in scan_source_text(
                source_path.read_text(encoding="utf-8"), path
            )
            if violation.rule in {"QML008", "QML009"}
        )
    assert violations == []
