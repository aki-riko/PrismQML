# coding: utf-8
# SPDX-License-Identifier: MIT
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Menu action keyboard accelerator runtime contract. 菜单动作键盘加速器运行时合同。

The accelerator must be a real keyboard binding: pressing the sequence has to run the
action, both while its menu is closed and while it is open, and a dynamic CanExecute
function has to gate it without touching the action.
加速器必须是真实键盘绑定：无论菜单关闭还是打开，按下快捷键都要真正执行动作；动态
CanExecute 函数必须能在不改动动作本身的情况下拦截它。
"""

from __future__ import annotations

import os
from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    Q_ARG,
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
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


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
SOURCE_PATH = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "menus" / "Action.qml"
)
ACCELERATOR_PATH = SOURCE_PATH.parent / "_internal" / "ActionAccelerator.qml"
LOGIC_PATH = SOURCE_PATH.parent / "_internal" / "ActionLogic.js"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "menu-accelerator-runtime.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "hostWindow"
    width: 420
    height: 300
    visible: true

    property bool commandEnabled: false
    property int openCount: 0
    property int blockedCount: 0
    property int disabledCount: 0
    property int plainCount: 0

    MenuCore {
        id: menu
        objectName: "menuCore"
        closeOnClickOutside: false

        Action {
            objectName: "openAction"
            actionId: "open"
            text: "Open"
            shortcut: "Ctrl+O"
            onTriggered: root.openCount += 1
        }

        Action {
            objectName: "blockedAction"
            actionId: "blocked"
            text: "Blocked"
            shortcut: "Ctrl+B"
            canExecute: function() { return root.commandEnabled }
            onTriggered: root.blockedCount += 1
        }

        Action {
            objectName: "disabledAction"
            actionId: "disabled"
            text: "Disabled"
            shortcut: "Ctrl+D"
            enabled: false
            onTriggered: root.disabledCount += 1
        }

        Action {
            objectName: "plainAction"
            actionId: "plain"
            text: "Plain"
            onTriggered: root.plainCount += 1
        }
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is accepted for accepted in allowed)
    ]


def _create_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isActive)
    return engine, component, window, warnings, windows_before


def _dispose_scene(qapp, engine, component, window) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()
    _pump(10)


def _action(window: QQuickWindow, object_name: str) -> QQuickItem:
    action = window.findChild(QQuickItem, object_name)
    assert action is not None, object_name
    return action


def _accelerator(action: QQuickItem) -> QObject | None:
    value = action.property("_accelerator")
    return value if isinstance(value, QObject) else None


def _press(window: QQuickWindow, key: Qt.Key, modifier: Qt.KeyboardModifier) -> None:
    QTest.keyClick(window, key, modifier)
    _pump(60)


def test_accelerator_runs_action_while_menu_is_closed(qapp):
    """Pressing the shortcut runs the action without opening the menu.

    菜单未打开时按下快捷键即可执行动作。
    """
    engine, component, window, warnings, windows_before = _create_scene(qapp)
    try:
        open_action = _action(window, "openAction")
        accelerator = _accelerator(open_action)
        assert accelerator is not None
        # Only a real QQuickShortcut exposes sequence/context/activated().
        accelerator_meta = accelerator.metaObject()
        assert accelerator_meta.indexOfProperty("sequence") >= 0
        assert accelerator_meta.indexOfProperty("context") >= 0
        assert accelerator_meta.indexOfSignal("activated()") >= 0
        assert accelerator.property("sequence") == "Ctrl+O"
        assert accelerator.property("context") == Qt.ShortcutContext.ApplicationShortcut
        assert accelerator.property("enabled")
        # The menu was never opened, so the row has no window of its own yet.
        assert open_action.window() is None
        assert not window.property("openCount")
        assert not _new_visible_windows(windows_before, window)

        _press(window, Qt.Key.Key_O, Qt.KeyboardModifier.ControlModifier)

        assert window.property("openCount") == 1
        assert _new_visible_windows(windows_before, window) == []
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_accelerator_ignores_disabled_and_shortcutless_rows(qapp):
    """A disabled row never fires, and a shortcut-less row owns no accelerator.

    禁用行绝不触发；没有快捷键的行不持有加速器。
    """
    engine, component, window, warnings, windows_before = _create_scene(qapp)
    try:
        disabled_action = _action(window, "disabledAction")
        plain_action = _action(window, "plainAction")
        assert _accelerator(disabled_action) is not None
        assert not _accelerator(disabled_action).property("enabled")
        assert _accelerator(plain_action) is None
        assert plain_action.property("shortcut") == ""

        _press(window, Qt.Key.Key_D, Qt.KeyboardModifier.ControlModifier)

        assert window.property("disabledCount") == 0
        assert window.property("plainCount") == 0

        # Clearing a live shortcut must remove the accelerator again.
        # 清空已生效的快捷键必须再次移除加速器。
        open_action = _action(window, "openAction")
        assert _accelerator(open_action) is not None
        open_action.setProperty("shortcut", "")
        assert _wait_for(lambda: _accelerator(open_action) is None)
        _press(window, Qt.Key.Key_O, Qt.KeyboardModifier.ControlModifier)
        assert window.property("openCount") == 0
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_accelerator_evaluates_dynamic_can_execute(qapp):
    """CanExecute is re-read on every press instead of being cached once.

    每次按下都会重新求值 CanExecute，而不是只缓存一次。
    """
    engine, component, window, warnings, windows_before = _create_scene(qapp)
    try:
        blocked_action = _action(window, "blockedAction")
        assert blocked_action.property("canExecuteNow") is False

        _press(window, Qt.Key.Key_B, Qt.KeyboardModifier.ControlModifier)
        assert window.property("blockedCount") == 0

        window.setProperty("commandEnabled", True)
        assert _wait_for(lambda: blocked_action.property("canExecuteNow") is True)

        _press(window, Qt.Key.Key_B, Qt.KeyboardModifier.ControlModifier)
        assert window.property("blockedCount") == 1

        window.setProperty("commandEnabled", False)
        assert _wait_for(lambda: blocked_action.property("canExecuteNow") is False)

        _press(window, Qt.Key.Key_B, Qt.KeyboardModifier.ControlModifier)
        assert window.property("blockedCount") == 1
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_accelerator_fires_and_closes_an_open_menu(qapp):
    """While the menu is open the shortcut runs the row and closes the menu.

    菜单打开时快捷键执行该行并关闭菜单。
    """
    engine, component, window, warnings, windows_before = _create_scene(qapp)
    try:
        menu = window.findChild(QQuickItem, "menuCore")
        assert menu is not None
        menu.setProperty("closeOnClickOutside", False)
        assert QMetaObject.invokeMethod(
            menu, "open", Q_ARG("QVariant", 200), Q_ARG("QVariant", 200)
        )
        assert _wait_for(lambda: menu.property("isOpen"))
        popup_window = _new_visible_windows(windows_before, window)
        assert len(popup_window) == 1

        _press(window, Qt.Key.Key_O, Qt.KeyboardModifier.ControlModifier)

        assert window.property("openCount") == 1
        assert _wait_for(lambda: not menu.property("isOpen"))
        assert _wait_for(lambda: _new_visible_windows(windows_before, window) == [])
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_accelerator_sources_use_application_scope_and_lazy_creation():
    """Source contract: application scope plus on-demand creation. 源码合同。"""
    source = SOURCE_PATH.read_text(encoding="utf-8")
    accelerator_source = ACCELERATOR_PATH.read_text(encoding="utf-8")
    logic_source = LOGIC_PATH.read_text(encoding="utf-8")

    assert 'import "_internal/ActionLogic.js" as ActionLogic' in source
    assert "ActionLogic.activate(control)" in source
    assert "function activate() { return ActionLogic.activate(control) }" in source
    assert "Qt.resolvedUrl(\"_internal/ActionAccelerator.qml\")" in source
    assert "if (shortcut === \"\") { _destroyAccelerator(); return }" in source
    assert "onShortcutChanged: _syncAccelerator()" in source
    # A Component.onCompleted handler would attach a QQmlComponentAttached object to every
    # row and break the idle-object contract of test_action_tooltip_timer_lifecycle.
    # Component.onCompleted 会给每一行附加 QQmlComponentAttached 对象, 破坏
    # test_action_tooltip_timer_lifecycle 的空闲对象合同。
    assert "Component.onCompleted" not in source
    assert "context: Qt.ApplicationShortcut" in accelerator_source
    assert "enabled: actionControl.enabled && actionControl.canExecuteNow" in accelerator_source
    assert "onActivated: actionControl.activate()" in accelerator_source
    assert "function canExecute(action)" in logic_source
    assert "function activate(action)" in logic_source
