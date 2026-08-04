# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Popup interaction stability regressions. 弹层交互稳定性回归测试。"""

import pytest

from PySide6.QtCore import QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtTest import QTest

from prismqml import register_types

from _button_dropdown_prewarm_support import (
    ROOT,
    _button,
    _button_dropdown,
    _create_scene,
    _dispose_scene,
    _dropdown_popup,
    _invoke,
    _popup_content,
    _visual_descendants,
    _wait_for,
    _pump,
)


MENU_SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "popup-interaction-menu.qml")
)
MENU_SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    property int triggerCount: 0

    function openMenu() {
        actionMenu.openAtControl(menuTarget)
    }

    width: 360
    height: 240

    Item {
        id: menuTarget
        x: 20
        y: 20
        width: 160
        height: 40
    }

    MenuCore {
        id: actionMenu
        objectName: "actionMenu"
        useQtPopupWindow: true

        Action {
            objectName: "dangerAction"
            text: "Danger"
            onTriggered: triggerCount += 1
        }
    }
}
"""


@pytest.fixture
def dropdown_scene(qapp):
    engine, component, root, warnings = _create_scene()
    window = QQuickWindow()
    window.setWidth(360)
    window.setHeight(240)
    root.setParentItem(window.contentItem())
    window.show()
    window.requestActivate()
    _pump(30)
    try:
        yield root, window, warnings
    finally:
        _dispose_scene(engine, component, root, window)


@pytest.fixture
def action_menu_scene(qapp):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(MENU_SCENE_SOURCE, MENU_SCENE_URL)
    assert _wait_for(
        lambda: component.status() != QQmlComponent.Status.Loading
    )
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    window = QQuickWindow()
    window.setWidth(360)
    window.setHeight(240)
    root.setParentItem(window.contentItem())
    window.show()
    window.requestActivate()
    _pump(30)
    try:
        yield root, window, warnings
    finally:
        root.setParentItem(None)
        window.hide()
        window.close()
        root.deleteLater()
        window.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump(20)


@pytest.mark.parametrize("object_name", ["dropdownButton", "splitButton"])
def test_menu_item_click_survives_opening_animation(
    dropdown_scene, object_name
):
    root, _window, warnings = dropdown_scene
    dropdown = _button_dropdown(_button(root, object_name))
    received = []
    dropdown.menuItemClicked.connect(
        lambda index, text: received.append((index, text))
    )

    _invoke(dropdown, "openMenu")
    popup = _dropdown_popup(dropdown)
    assert _wait_for(lambda: popup.property("isOpen"))
    _pump(20)
    assert popup.property("_scale") < 1.0

    item = next(
        child
        for child in _visual_descendants(_popup_content(popup))
        if child.metaObject().indexOfProperty("isSeparator") >= 0
        and child.property("text") == "Alpha"
    )
    popup_window = item.window()
    assert popup_window is not None
    click_position = item.mapToScene(
        QPointF(item.width() / 2, item.height() / 2)
    ).toPoint()
    QTest.mousePress(
        popup_window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        click_position,
    )
    stabilized_scale = popup.property("_scale")
    stabilized_global = item.mapToGlobal(
        QPointF(item.width() / 2, item.height() / 2)
    )
    _pump(100)
    release_global = item.mapToGlobal(
        QPointF(item.width() / 2, item.height() / 2)
    )
    QTest.mouseRelease(
        popup_window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        click_position,
    )
    _pump(20)

    assert stabilized_scale == pytest.approx(1.0)
    assert release_global.x() == pytest.approx(stabilized_global.x(), abs=0.5)
    assert release_global.y() == pytest.approx(stabilized_global.y(), abs=0.5)
    assert received == [(0, "Alpha")]
    assert warnings == []


@pytest.mark.parametrize("popup_mode", ["qt_window", "in_window"])
def test_action_click_survives_opening_animation(
    action_menu_scene, popup_mode
):
    root, _window, warnings = action_menu_scene
    menu = root.findChild(type(root), "actionMenu")
    action = root.findChild(type(root), "dangerAction")
    assert menu is not None
    assert action is not None
    menu.setProperty("useQtPopupWindow", popup_mode == "qt_window")
    menu.setProperty("useInWindowPopup", popup_mode == "in_window")

    _invoke(root, "openMenu")
    assert _wait_for(lambda: menu.property("isOpen"))
    _pump(20)
    assert menu.property("_scale") < 1.0
    popup_window = action.window()
    assert popup_window is not None
    click_position = action.mapToScene(
        QPointF(action.width() / 2, action.height() / 2)
    ).toPoint()

    QTest.mousePress(
        popup_window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        click_position,
    )
    stabilized_scale = menu.property("_scale")
    _pump(100)
    QTest.mouseRelease(
        popup_window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        click_position,
    )
    _pump(20)

    assert stabilized_scale == pytest.approx(1.0)
    assert root.property("triggerCount") == 1
    assert warnings == []
