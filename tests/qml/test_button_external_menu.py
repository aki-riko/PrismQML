# coding: utf-8
# SPDX-License-Identifier: MIT
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""真实外部菜单与 Dropdown/Split 组合回归。"""

from __future__ import annotations

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPointF,
    QUrl,
    QTimer,
    Qt,
    qInstallMessageHandler,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


SCENE_URL = QUrl.fromLocalFile(__file__.replace("test_button_external_menu.py", "button-external-menu.qml"))
SCENE_SOURCE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    width: 520
    height: 280
    visible: true
    property int dropdownMainClicks: 0
    property int splitMainClicks: 0
    property int dropdownOpening: 0
    property int splitOpening: 0
    MenuCore {
        id: dropdownMenu
        objectName: "externalDropdownMenu"
        useInWindowPopup: true
        Action { actionId: "dropdown-one"; text: "外部菜单一" }
        Action {
            actionId: "dropdown-two"
            text: "外部菜单二（用于验证重挂载后宽度仍完整保留的超长文本）"
        }
    }

    MenuCore {
        id: splitMenu
        objectName: "externalSplitMenu"
        useInWindowPopup: true
        Action { text: "分离菜单一" }
        Action { text: "分离菜单二" }
    }

    QtObject { id: invalidMenu; objectName: "invalidMenu" }

    Button {
        id: dropdownButton
        objectName: "externalDropdownButton"
        x: 30
        y: 30
        width: 190
        height: 42
        feature: Enums.button.feature_dropdown
        text: "外部下拉"
        menuItems: ["不应显示的回退项"]
        menu: dropdownMenu
        onClicked: root.dropdownMainClicks += 1
        onMenuAboutToOpen: root.dropdownOpening += 1
    }

    Button {
        id: splitButton
        objectName: "externalSplitButton"
        x: 30
        y: 100
        width: 190
        height: 42
        feature: Enums.button.feature_split
        text: "外部分离"
        menu: splitMenu
        onClicked: root.splitMainClicks += 1
        onMenuAboutToOpen: root.splitOpening += 1
    }

    Button {
        id: invalidButton
        objectName: "invalidMenuButton"
        x: 30
        y: 170
        width: 190
        height: 42
        feature: Enums.button.feature_dropdown
        text: "非法菜单"
        menu: invalidMenu
    }
}
""".encode("utf-8")


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1200) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isActive)
    return engine, component, window, warnings


def _button(window, object_name: str) -> QQuickItem:
    button = window.findChild(QQuickItem, object_name)
    assert button is not None
    return button


def _menu(window, object_name: str) -> QQuickItem:
    menu = window.findChild(QQuickItem, object_name)
    assert menu is not None
    return menu


def _click(window: QQuickWindow, button: QQuickItem, arrow: bool = False) -> None:
    x = button.width() - 16 if arrow else 40
    target = button.mapToScene(QPointF(x, button.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        target.toPoint(),
    )


def _dispose(engine, component, window) -> None:
    for name in ("externalDropdownMenu", "externalSplitMenu"):
        menu = window.findChild(QQuickItem, name)
        if menu is not None and menu.property("isOpen"):
            menu.close()
    _pump(30)
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(20)


def test_dropdown_and_split_delegate_to_external_menu(qapp):
    engine, component, window, warnings = _create_scene()
    try:
        dropdown = _button(window, "externalDropdownButton")
        split = _button(window, "externalSplitButton")
        dropdown_menu = _menu(window, "externalDropdownMenu")
        split_menu = _menu(window, "externalSplitMenu")

        _click(window, dropdown)
        assert _wait_for(lambda: dropdown_menu.property("isOpen"))
        assert window.property("dropdownOpening") == 1
        assert window.property("dropdownMainClicks") == 0

        dropdown_menu.close()
        assert _wait_for(
            lambda: not dropdown_menu.property("isOpen")
            and not dropdown_menu.property("isClosing")
        )

        _click(window, split)
        assert window.property("splitMainClicks") == 1
        assert not split_menu.property("isOpen")

        _click(window, split, arrow=True)
        assert _wait_for(lambda: split_menu.property("isOpen"))
        assert window.property("splitOpening") == 1
        assert window.property("splitMainClicks") == 1
        assert not warnings
    finally:
        _dispose(engine, component, window)


def test_external_menu_toggles_and_prewarms_without_internal_fallback(qapp):
    engine, component, window, warnings = _create_scene()
    try:
        dropdown = _button(window, "externalDropdownButton")
        menu = _menu(window, "externalDropdownMenu")
        dropdown_modules = [
            item for item in dropdown.findChildren(QQuickItem)
            if item.metaObject().indexOfProperty("isMenuOpen") >= 0
        ]
        assert len(dropdown_modules) == 1
        internal_menu = next(
            item for item in dropdown_modules[0].findChildren(QQuickItem)
            if item.metaObject().indexOfProperty("_itemsHeight") >= 0
        )

        dropdown.forceActiveFocus()
        assert _wait_for(lambda: menu.property("_prewarmed"))
        assert not menu.property("isOpen")
        assert not internal_menu.property("isOpen")

        dropdown_modules[0].openMenu()
        assert _wait_for(lambda: menu.property("isOpen"))
        dropdown_modules[0].openMenu()
        assert _wait_for(lambda: not menu.property("isOpen"))
        assert not internal_menu.property("isOpen")
        assert not warnings
    finally:
        _dispose(engine, component, window)


def test_in_window_external_menu_preserves_geometry_and_action_lifecycle(qapp):
    """Popup.Item 重挂载不得丢失多行尺寸或声明式 Action API。"""
    engine, component, window, warnings = _create_scene()
    try:
        dropdown = _button(window, "externalDropdownButton")
        menu = _menu(window, "externalDropdownMenu")
        first = menu.getAction("dropdown-one")
        second = menu.getAction("dropdown-two")
        assert first is not None
        assert second is not None
        expected_height = first.height() + second.height()

        _click(window, dropdown)
        assert _wait_for(lambda: menu.property("isOpen"))
        assert menu.property("popupHeight") >= expected_height
        assert menu.property("popupWidth") > menu.property("minWidth"), {
            "popup_width": menu.property("popupWidth"),
            "first_width": first.width(),
            "first_implicit_width": first.implicitWidth(),
            "first_children_rect": first.childrenRect(),
            "second_width": second.width(),
            "second_implicit_width": second.implicitWidth(),
            "second_children_rect": second.childrenRect(),
        }

        menu.close()
        assert _wait_for(
            lambda: not menu.property("isOpen")
            and not menu.property("isClosing")
        )
        menu.clear()
        assert _wait_for(
            lambda: menu.getAction("dropdown-one") is None
            and menu.getAction("dropdown-two") is None
        )

        dynamic_one = menu.addAction(
            "动态菜单一", "", "", {"actionId": "dynamic-one"}
        )
        dynamic_two = menu.addAction(
            "动态菜单二", "", "", {"actionId": "dynamic-two"}
        )
        assert menu.getAction("dynamic-one") is not None
        assert menu.getAction("dynamic-two") is not None

        _click(window, dropdown)
        assert _wait_for(lambda: menu.property("isOpen"))
        assert menu.property("popupHeight") >= dynamic_one.height() + dynamic_two.height()
        menu.close()
        assert _wait_for(
            lambda: not menu.property("isOpen")
            and not menu.property("isClosing")
        )
        assert menu.removeAction("dynamic-one")
        assert _wait_for(lambda: menu.getAction("dynamic-one") is None)
        assert menu.getAction("dynamic-two") is not None
        assert not warnings
    finally:
        _dispose(engine, component, window)


def test_invalid_external_menu_reports_contract_warning(qapp):
    engine, component, window, warnings = _create_scene()
    try:
        messages = []
        previous_handler = qInstallMessageHandler(
            lambda _message_type, _context, message: messages.append(message)
        )
        button = _button(window, "invalidMenuButton")
        modules = [
            item for item in button.findChildren(QQuickItem)
            if item.metaObject().indexOfProperty("isMenuOpen") >= 0
        ]
        assert len(modules) == 1
        modules[0].openMenu()
        qInstallMessageHandler(previous_handler)
        assert any("Button.menu" in message and "openAtControl" in message for message in messages)
        assert not modules[0].property("isMenuOpen")
        assert not warnings
    finally:
        qInstallMessageHandler(None)
        _dispose(engine, component, window)
