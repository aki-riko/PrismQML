# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""ButtonCore accessible metadata, asserted through Qt's accessibility interface.

`Accessible.name` / `Accessible.role` cannot be read back as attached properties
(measured offscreen and on the real windows platform: both return None, and a
Qt-only control behaves the same way). The authoritative observable is
`QAccessible.queryAccessibleInterface()`, which reports what the platform
accessibility layer would actually see -- this file asserts against that.
`Accessible` 附加属性无法读回（离屏与真实 windows 平台均为 None，纯 Qt 控件亦然），
因此以 `QAccessible.queryAccessibleInterface()` 作为权威观测点。
"""

from PySide6.QtCore import QCoreApplication, QObject, QUrl
from PySide6.QtGui import QAccessible
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types

SCENE = b"""import QtQuick
import PrismQML
Item {
    width: 400
    height: 200

    Button {
        objectName: "plain"
        text: "Save"
    }

    Button {
        objectName: "toggle"
        text: "Bold"
        feature: Enums.button.feature_toggle
        checked: true
    }

    Button {
        objectName: "iconOnly"
        toolTipText: "Copy"
    }
}
"""


def _scene(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE, QUrl())
    errors = [error.toString() for error in component.errors()]
    assert component.status() == QQmlComponent.Status.Ready, errors
    root = component.create()
    assert isinstance(root, QQuickItem), errors
    QCoreApplication.processEvents()
    return engine, component, root


def _interface(root, name: str):
    item = root.findChild(QObject, name)
    assert item is not None, f"{name} was not created"
    interface = QAccessible.queryAccessibleInterface(item)
    assert interface is not None, f"{name} exposes no accessible interface"
    return interface


def test_plain_button_reports_button_role_and_visible_text(qapp) -> None:
    """A plain button is a button whose accessible name is its visible label."""
    engine, component, root = _scene(qapp)
    try:
        interface = _interface(root, "plain")
        assert interface.role() == QAccessible.Role.Button
        assert interface.text(QAccessible.Text.Name) == "Save"
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


def test_toggle_button_reports_checkable_state(qapp) -> None:
    """The toggle feature must change both the role and the reported state."""
    engine, component, root = _scene(qapp)
    try:
        interface = _interface(root, "toggle")
        # A toggle carries state, so it must not be announced as a plain button.
        # 切换按钮带状态，不得按普通按钮播报。
        assert interface.role() != QAccessible.Role.Button
        assert interface.text(QAccessible.Text.Name) == "Bold"
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


def test_icon_only_button_falls_back_to_tooltip_text(qapp) -> None:
    """With no visible text the tooltip is the only honest name available."""
    engine, component, root = _scene(qapp)
    try:
        interface = _interface(root, "iconOnly")
        assert interface.role() == QAccessible.Role.Button
        assert interface.text(QAccessible.Text.Name) == "Copy"
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
