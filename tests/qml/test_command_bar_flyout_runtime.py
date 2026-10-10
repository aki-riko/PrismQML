# coding: utf-8
# SPDX-License-Identifier: MIT
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""CommandBarFlyout runtime contract. 命令浮出层运行时合同。

The flyout must open as its own native popup window (AGENTS.md 4.8) and drive a real
collapsed / mini-expanded / expanded state machine over CommandBar content.
浮出层必须以独立原生弹层窗口打开，并在 CommandBar 内容上驱动真实的
折叠 / 迷你展开 / 完全展开状态机。
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
    QPointF,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
MENUS_ROOT = ROOT / "prismqml" / "PrismQML" / "controls" / "menus"
FLYOUT_PATH = MENUS_ROOT / "CommandBarFlyout.qml"
SURFACE_PATH = MENUS_ROOT / "_internal" / "CommandBarFlyoutSurface.qml"
ENUM_PATH = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "CommandBar.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "command-bar-flyout-runtime.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/menus" as Menus
import "../../prismqml/PrismQML/controls/buttons" as Buttons

Window {
    id: root
    objectName: "hostWindow"
    width: 520
    height: 320
    visible: true

    readonly property string cutIcon: Enums.icon.cut
    readonly property string moreIcon: Enums.icon.more_horizontal
    readonly property string chevronUpIcon: Enums.icon.chevron_up
    readonly property string chevronDownIcon: Enums.icon.chevron_down
    readonly property int collapsedState: Enums.commandBar.flyout_collapsed
    readonly property int miniExpandedState: Enums.commandBar.flyout_mini_expanded
    readonly property int expandedState: Enums.commandBar.flyout_expanded
    property int primaryHits: 0
    property int secondaryHits: 0
    property var primaryCommands: [
        { "text": "Cut", "icon": Enums.icon.cut },
        { "text": "Copy", "icon": Enums.icon.copy },
        { "text": "Paste", "icon": Enums.icon.clipboard }
    ]
    property var secondaryCommands: [
        { "text": "Select all", "icon": Enums.icon.select_all_on },
        { "text": "Undo", "icon": Enums.icon.arrow_undo }
    ]

    Buttons.Button {
        id: targetButton
        objectName: "flyoutTarget"
        x: 24
        y: 24
        width: 140
        height: 32
        text: "Commands"
    }

    Menus.CommandBarFlyout {
        id: flyout
        objectName: "commandBarFlyout"
        primaryCommands: root.primaryCommands
        secondaryCommands: root.secondaryCommands
        onActionTriggered: root.primaryHits += 1
        onSecondaryActionTriggered: root.secondaryHits += 1
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
    flyout = window.findChild(QQuickItem, "commandBarFlyout")
    target = window.findChild(QQuickItem, "flyoutTarget")
    assert flyout is not None and target is not None
    _pump()
    return engine, component, window, flyout, target, warnings, windows_before


def _dispose_scene(qapp, engine, component, window) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()
    _pump(10)


def _show_flyout(window, flyout, target, windows_before):
    assert QMetaObject.invokeMethod(flyout, "show", Q_ARG("QVariant", target))
    assert _wait_for(lambda: flyout.property("isOpen"))
    popup_windows = _new_visible_windows(windows_before, window)
    assert len(popup_windows) == 1, [
        candidate.title() for candidate in popup_windows
    ]
    return popup_windows[0]


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    # Popup content is reparented visually into the native window, while its QObject
    # parent stays with the flyout, so objectName lookups must walk the visual tree.
    # 弹层内容在视觉上被重挂到原生窗口, 但其 QObject 父级仍是浮出层, 因此按 objectName
    # 查找必须遍历视觉树。
    result: list[QQuickItem] = []
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def _named(popup_window: QQuickWindow, name: str) -> QQuickItem:
    matches = [
        item
        for item in _visual_descendants(popup_window.contentItem())
        if item.objectName() == name
    ]
    assert len(matches) == 1, (name, [item.objectName() for item in matches])
    return matches[0]


def _buttons_by_icon(popup_window: QQuickWindow, icon: str) -> list[QQuickItem]:
    return [
        child
        for child in _visual_descendants(popup_window.contentItem())
        if child.metaObject().indexOfProperty("contentAlignment") >= 0
        and child.property("icon") == icon
    ]


def _secondary_buttons(popup_window: QQuickWindow) -> list[QQuickItem]:
    matches = [
        child
        for child in _visual_descendants(popup_window.contentItem())
        if child.metaObject().indexOfProperty("contentAlignment") >= 0
        and str(child.objectName()).startswith("commandBarFlyoutSecondaryAction")
    ]
    return sorted(matches, key=lambda item: item.objectName())


def test_flyout_opens_as_its_own_native_window(qapp):
    """The flyout must be an independent QWindow, left-aligned with its trigger.

    浮出层必须是独立 QWindow，并与触发控件左对齐。
    """
    engine, component, window, flyout, target, warnings, windows_before = _create_scene(
        qapp
    )
    try:
        assert flyout.property("useInWindowPopup") is False
        assert flyout.property("useQtPopupWindow") is False
        assert flyout.property("isOpen") is False

        popup_window = _show_flyout(window, flyout, target, windows_before)
        assert isinstance(popup_window, QQuickWindow)
        assert popup_window.isVisible()
        assert flyout.property("popupWidth") > 0
        assert flyout.property("popupHeight") > 0

        target_global = target.mapToGlobal(QPointF(0, 0))
        assert popup_window.x() + flyout.property("_panelOffset") == target_global.x()

        assert QMetaObject.invokeMethod(flyout, "close")
        assert _wait_for(lambda: not flyout.property("isOpen"))
        assert _wait_for(lambda: _new_visible_windows(windows_before, window) == [])
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_expansion_state_machine_steps_forward_and_back(qapp):
    """collapsed → mini-expanded → expanded and back again.

    折叠 → 迷你展开 → 完全展开，并能原路回退。
    """
    engine, component, window, flyout, target, warnings, windows_before = _create_scene(
        qapp
    )
    try:
        collapsed = window.property("collapsedState")
        mini = window.property("miniExpandedState")
        expanded = window.property("expandedState")
        assert flyout.property("expansionState") == collapsed
        assert flyout.property("expanded") is False
        assert flyout.property("fullyExpanded") is False

        _show_flyout(window, flyout, target, windows_before)

        assert QMetaObject.invokeMethod(flyout, "expand")
        assert flyout.property("expansionState") == mini
        assert flyout.property("expanded") is True
        assert flyout.property("fullyExpanded") is False

        assert QMetaObject.invokeMethod(flyout, "expand")
        assert flyout.property("expansionState") == expanded
        assert flyout.property("fullyExpanded") is True

        assert QMetaObject.invokeMethod(flyout, "collapse")
        assert flyout.property("expansionState") == mini
        assert QMetaObject.invokeMethod(flyout, "collapse")
        assert flyout.property("expansionState") == collapsed
        assert flyout.property("expanded") is False

        assert QMetaObject.invokeMethod(flyout, "toggleSecondary")
        assert flyout.property("expansionState") == mini
        assert QMetaObject.invokeMethod(flyout, "toggleExpanded")
        assert flyout.property("expansionState") == expanded
        assert QMetaObject.invokeMethod(flyout, "toggleExpanded")
        assert flyout.property("expansionState") == mini
        assert QMetaObject.invokeMethod(flyout, "toggleSecondary")
        assert flyout.property("expansionState") == collapsed

        assert QMetaObject.invokeMethod(flyout, "close")
        assert _wait_for(lambda: _new_visible_windows(windows_before, window) == [])
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_secondary_row_and_labels_follow_the_state_machine(qapp):
    """The mini-expanded row appears compact and gains labels when expanded.

    迷你展开行先以紧凑形态出现，完全展开后获得标签。
    """
    engine, component, window, flyout, target, warnings, windows_before = _create_scene(
        qapp
    )
    try:
        popup_window = _show_flyout(window, flyout, target, windows_before)
        more_button = _named(popup_window, "commandBarFlyoutMoreButton")
        expand_button = _named(popup_window, "commandBarFlyoutExpandButton")
        assert more_button.property("visible") is True
        assert more_button.property("icon") == window.property("moreIcon")
        assert expand_button.property("visible") is False

        assert QMetaObject.invokeMethod(more_button, "click")
        assert flyout.property("expansionState") == window.property("miniExpandedState")
        assert more_button.property("icon") == window.property("chevronUpIcon")
        assert expand_button.property("visible") is True
        assert expand_button.property("icon") == window.property("chevronDownIcon")

        secondary_buttons = _secondary_buttons(popup_window)
        assert len(secondary_buttons) == 2
        assert [button.property("visible") for button in secondary_buttons] == [
            True,
            True,
        ]
        assert [button.property("text") for button in secondary_buttons] == ["", ""]

        assert QMetaObject.invokeMethod(expand_button, "click")
        assert flyout.property("expansionState") == window.property("expandedState")
        assert expand_button.property("icon") == window.property("chevronUpIcon")
        assert [button.property("text") for button in secondary_buttons] == [
            "Select all",
            "Undo",
        ]

        assert QMetaObject.invokeMethod(more_button, "click")
        assert flyout.property("expansionState") == window.property("collapsedState")
        assert [button.property("visible") for button in secondary_buttons] == [
            False,
            False,
        ]
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_primary_and_secondary_commands_trigger_and_close(qapp):
    """A command click reaches the consumer and closes the flyout.

    命令点击触达消费者并关闭浮出层。
    """
    engine, component, window, flyout, target, warnings, windows_before = _create_scene(
        qapp
    )
    try:
        popup_window = _show_flyout(window, flyout, target, windows_before)
        cut_buttons = _buttons_by_icon(popup_window, window.property("cutIcon"))
        assert len(cut_buttons) == 1
        assert QMetaObject.invokeMethod(cut_buttons[0], "click")
        assert _wait_for(lambda: window.property("primaryHits") == 1)
        assert _wait_for(lambda: not flyout.property("isOpen"))
        assert _wait_for(lambda: _new_visible_windows(windows_before, window) == [])

        popup_window = _show_flyout(window, flyout, target, windows_before)
        assert QMetaObject.invokeMethod(flyout, "toggleSecondary")
        secondary_buttons = _secondary_buttons(popup_window)
        assert len(secondary_buttons) == 2
        assert QMetaObject.invokeMethod(secondary_buttons[1], "click")
        assert _wait_for(lambda: window.property("secondaryHits") == 1)
        assert _wait_for(lambda: not flyout.property("isOpen"))
        assert _wait_for(lambda: _new_visible_windows(windows_before, window) == [])
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_flyout_never_degrades_to_an_in_window_popup():
    """Source contract: native popup base plus Enums-only styling. 源码合同。"""
    flyout_source = FLYOUT_PATH.read_text(encoding="utf-8")
    surface_source = SURFACE_PATH.read_text(encoding="utf-8")
    enum_source = ENUM_PATH.read_text(encoding="utf-8")
    qmldir_source = (MENUS_ROOT / "qmldir").read_text(encoding="utf-8")

    assert "PopupWindowCore {" in flyout_source
    assert "useInWindowPopup" not in flyout_source
    assert "useQtPopupWindow" not in flyout_source
    assert "QtQuick.Controls" not in flyout_source
    assert "import QtQuick 2" not in flyout_source
    assert "CommandBar {" in surface_source
    assert "required property var flyout" in surface_source
    for state in ("flyout_collapsed", "flyout_mini_expanded", "flyout_expanded"):
        assert f"readonly property int {state}:" in enum_source
    assert "CommandBarFlyout CommandBarFlyout.qml" in qmldir_source
