# coding: utf-8
# SPDX-License-Identifier: MIT
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Radio menu row mutual exclusion contract. 菜单单选行互斥合同。

RadioMenuFlyoutItem rows must behave as one single-choice group: selecting a row clears
the other checked rows of the same group, groups stay isolated from each other, and a
plain checkable row keeps the pre-existing toggle behaviour.
单选行必须表现为一个单选组：选中某行会清除同组其它已选行，不同组互不影响，普通可勾选行
保持既有切换行为。
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
MENUS_ROOT = ROOT / "prismqml" / "PrismQML" / "controls" / "menus"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "radio-menu-group-runtime.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/menus" as Menus

Window {
    id: root
    objectName: "hostWindow"
    width: 420
    height: 300
    visible: true

    readonly property int indicatorIconSize: Enums.iconSize.xs
    readonly property int indicatorWidth: Enums.spacing.xl
    readonly property string radioIcon: Enums.icon.radio_button
    readonly property string checkIcon: Enums.icon.checkmark
    property int triggeredCount: 0

    Menus.MenuCore {
        id: menu
        objectName: "menuCore"
        closeOnClickOutside: false

        Menus.RadioMenuFlyoutItem {
            objectName: "alignLeft"
            actionId: "left"
            text: "Left"
            checked: true
            onTriggered: root.triggeredCount += 1
        }

        Menus.RadioMenuFlyoutItem {
            objectName: "alignCenter"
            actionId: "center"
            text: "Center"
            onTriggered: root.triggeredCount += 1
        }

        Menus.RadioMenuFlyoutItem {
            objectName: "alignRight"
            actionId: "right"
            text: "Right"
            onTriggered: root.triggeredCount += 1
        }

        Action {
            objectName: "zoom100"
            actionId: "zoom100"
            text: "100%"
            radioGroup: "zoom"
            checked: true
        }

        Action {
            objectName: "zoom200"
            actionId: "zoom200"
            text: "200%"
            radioGroup: "zoom"
        }

        Action {
            objectName: "zoom50"
            actionId: "zoom50"
            text: "50%"
            radioGroup: "zoom"
            exclusive: false
        }

        Action {
            objectName: "bold"
            actionId: "bold"
            text: "Bold"
            checkable: true
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
    _pump()
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


def _activate(action: QQuickItem) -> bool:
    return bool(QMetaObject.invokeMethod(action, "activate"))


def _indicator(action: QQuickItem, indicator_size: int, indicator_width: int) -> QQuickItem:
    # The indicator is the only xs icon that also claims the leading gutter width;
    # the submenu arrow shares the icon size but not the gutter width.
    # 指示器是唯一同时占用前导槽宽度的 xs 图标; 子菜单箭头图标尺寸相同但槽宽度不同。
    matches = [
        child
        for child in action.findChildren(QQuickItem)
        if child.metaObject().indexOfProperty("iconSize") >= 0
        and child.property("iconSize") == indicator_size
        and child.property("width") == indicator_width
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _checked(window: QQuickWindow, *names: str) -> list[bool]:
    return [_action(window, name).property("checked") for name in names]


def test_radio_rows_share_the_default_group(qapp):
    """Selecting one radio row clears the other rows of the same group.

    选中一个单选行会清除同组其它行。
    """
    engine, component, window, warnings, windows_before = _create_scene(qapp)
    try:
        left = _action(window, "alignLeft")
        center = _action(window, "alignCenter")
        right = _action(window, "alignRight")

        assert left.property("radioGroup") == "default"
        assert left.property("radioMode") is True
        assert _checked(window, "alignLeft", "alignCenter", "alignRight") == [
            True,
            False,
            False,
        ]

        assert _activate(center)
        assert _checked(window, "alignLeft", "alignCenter", "alignRight") == [
            False,
            True,
            False,
        ]

        assert _activate(right)
        assert _checked(window, "alignLeft", "alignCenter", "alignRight") == [
            False,
            False,
            True,
        ]

        # Another group keeps its own selection 其它组保持自己的选中项
        assert _action(window, "zoom100").property("checked") is True
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_named_radio_groups_stay_isolated(qapp):
    """A named group only clears rows carrying the same group name.

    具名组只清除同名组的行。
    """
    engine, component, window, warnings, windows_before = _create_scene(qapp)
    try:
        assert _activate(_action(window, "zoom200"))
        assert _checked(window, "zoom100", "zoom200") == [False, True]
        assert _action(window, "alignLeft").property("checked") is True

        # exclusive: false keeps the other checked rows of the group
        # exclusive: false 保留同组其它已选行
        assert _activate(_action(window, "zoom50"))
        assert _checked(window, "zoom200", "zoom50") == [True, True]
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_checkable_row_keeps_toggle_semantics_and_check_glyph(qapp):
    """A plain checkable row still toggles and still shows the check mark.

    普通可勾选行仍然切换，并继续显示勾选图标。
    """
    engine, component, window, warnings, windows_before = _create_scene(qapp)
    try:
        bold = _action(window, "bold")
        assert bold.property("radioMode") is False

        assert _activate(bold)
        assert bold.property("checked") is True
        assert _activate(bold)
        assert bold.property("checked") is False

        indicator_size = window.property("indicatorIconSize")
        indicator_width = window.property("indicatorWidth")
        radio_indicator = _indicator(
            _action(window, "alignLeft"), indicator_size, indicator_width
        )
        assert radio_indicator.property("icon") == window.property("radioIcon")

        assert _activate(_action(window, "alignCenter"))
        check_indicator = _indicator(bold, indicator_size, indicator_width)
        assert check_indicator.property("icon") == window.property("checkIcon")
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_pointer_click_selects_a_radio_row_inside_the_open_menu(qapp):
    """A real pointer click on the row runs the same mutual exclusion.

    对菜单行的真实指针点击走同一套互斥逻辑。
    """
    engine, component, window, warnings, windows_before = _create_scene(qapp)
    try:
        menu = window.findChild(QQuickItem, "menuCore")
        assert menu is not None
        assert QMetaObject.invokeMethod(
            menu, "open", Q_ARG("QVariant", 200), Q_ARG("QVariant", 200)
        )
        assert _wait_for(lambda: menu.property("isOpen"))
        popup_windows = _new_visible_windows(windows_before, window)
        assert len(popup_windows) == 1
        popup_window = popup_windows[0]

        center = _action(window, "alignCenter")
        interaction = center.findChild(QQuickItem, "actionInteraction")
        assert interaction is not None
        indicator_size = window.property("indicatorIconSize")
        indicator_width = window.property("indicatorWidth")
        left_indicator = _indicator(
            _action(window, "alignLeft"), indicator_size, indicator_width
        )
        center_indicator = _indicator(center, indicator_size, indicator_width)
        # Once the rows live in the open popup window, effective visibility is real.
        # 行进入已打开的弹层窗口后, 有效可见性才真实可判。
        assert left_indicator.property("visible") is True
        assert center_indicator.property("visible") is False

        click_position = interaction.mapToScene(
            QPointF(interaction.width() / 2, interaction.height() / 2)
        ).toPoint()
        QTest.mouseClick(
            popup_window, Qt.MouseButton.LeftButton, pos=click_position
        )
        _pump(80)

        assert _checked(window, "alignLeft", "alignCenter") == [False, True]
        assert center_indicator.property("visible") is True
        assert window.property("triggeredCount") >= 1
        assert _wait_for(lambda: not menu.property("isOpen"))
        assert _wait_for(lambda: _new_visible_windows(windows_before, window) == [])
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_radio_sources_and_registration_contract():
    """Source contract for the radio semantics and qmldir registration. 源码与注册合同。"""
    action_source = (MENUS_ROOT / "Action.qml").read_text(encoding="utf-8")
    radio_source = (MENUS_ROOT / "RadioMenuFlyoutItem.qml").read_text(encoding="utf-8")
    qmldir_source = (MENUS_ROOT / "qmldir").read_text(encoding="utf-8")

    assert 'property string radioGroup: ""' in action_source
    assert "property bool exclusive: true" in action_source
    assert "readonly property bool radioMode: radioGroup !== \"\"" in action_source
    assert "Enums.icon.radio_button : Enums.icon.checkmark" in action_source
    logic_source = (MENUS_ROOT / "_internal" / "ActionLogic.js").read_text(
        encoding="utf-8"
    )
    assert "if (action.radioMode) {" in logic_source
    assert "function clearGroup(action)" in logic_source
    assert "Action {" in radio_source
    assert 'radioGroup: "default"' in radio_source
    assert "RadioMenuFlyoutItem RadioMenuFlyoutItem.qml" in qmldir_source
