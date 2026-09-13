# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""鼠标坐标菜单不得被控件锚点跟踪覆盖。"""

from PySide6.QtCore import QMetaObject

from test_popup_window_animation_metrics import _pump
from test_skin_scope import _build, engine  # noqa: F401


SCENE = """
import QtQuick
import QtQuick.Window
import PrismQML as Fluent

Window {
    width: 640; height: 480
    visible: false
    property real expectedX: 0
    property real expectedY: 0
    readonly property real menuX: menu._popupWindow ? menu._popupWindow.x : 0
    readonly property real menuY: menu._popupWindow ? menu._popupWindow.y : 0
    function openMenu() {
        var pos = trigger.mapToGlobal(73, 41)
        expectedX = pos.x
        expectedY = pos.y
        menu.popup(73, 41, trigger)
    }
    function closeMenu() { menu.close() }
    Item { id: trigger; x: 80; y: 60; width: 240; height: 160 }
    Fluent.PopupWindowCore {
        id: menu
        popupWidth: 100
        popupHeight: 60
    }
}
"""


def test_popup_keeps_requested_mouse_position_after_event_processing(engine):
    component, root = _build(engine, SCENE)
    try:
        assert QMetaObject.invokeMethod(root, "openMenu")
        _pump(300)
        assert (root.property("menuX"), root.property("menuY")) == (
            root.property("expectedX"), root.property("expectedY")
        )
    finally:
        QMetaObject.invokeMethod(root, "closeMenu")
        _pump(300)
        root.close()
