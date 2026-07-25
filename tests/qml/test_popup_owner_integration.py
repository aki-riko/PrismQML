# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""PopupWindowCore owner repair integration. 弹层 owner 修复集成测试。"""

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QTimer,
    QUrl,
    Slot,
)
from PySide6.QtGui import QWindow
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


SCENE_URL = QUrl.fromLocalFile(__file__.replace(".py", ".qml"))
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    width: 360
    height: 240
    visible: true

    function prewarmMenu() { popup.prewarm() }
    function openMenu() { popup.openAtControl(target) }
    function resetMenu() { popup.forceReset() }

    Item {
        id: target
        x: 20
        y: 20
        width: 120
        height: 40
    }

    PopupWindowCore {
        id: popup
        objectName: "ownerRepairPopup"
        popupWidth: 220
        popupHeight: 120
        useQtPopupWindow: true
    }
}
"""


class _CountingWindowHelper(QObject):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.calls = []

    @Slot("QVariant", "QVariant", result=bool)
    def ensurePopupWindowOwner(self, popup_window, owner_window) -> bool:
        self.calls.append((popup_window, owner_window))
        return True


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _invoke(obj, method: str) -> None:
    assert QMetaObject.invokeMethod(obj, method), method


def _create_scene():
    engine = QQmlApplicationEngine()
    register_types(engine)
    helper = _CountingWindowHelper(engine)
    engine.rootContext().setContextProperty("WindowHelper", helper)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert isinstance(root, QWindow), [
        error.toString() for error in component.errors()
    ]
    root.requestActivate()
    _pump(40)
    return engine, component, root, helper


def _dispose_scene(engine, component, root) -> None:
    _invoke(root, "resetMenu")
    _pump(20)
    root.close()
    root.deleteLater()
    component.deleteLater()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(20)


def test_cold_open_repairs_owner_and_close_cancels_queued_work(qapp):
    engine, component, root, helper = _create_scene()
    try:
        _invoke(root, "openMenu")
        _pump(40)

        assert helper.calls
        assert all(owner is root for _, owner in helper.calls)
        assert all(
            popup.metaObject().className() == "QQuickPopupWindow"
            for popup, _ in helper.calls
        )

        _invoke(root, "resetMenu")
        _pump(20)
        calls_after_close = len(helper.calls)
        _pump(40)
        assert len(helper.calls) == calls_after_close
    finally:
        _dispose_scene(engine, component, root)


def test_first_prewarm_repairs_the_created_qt_popup_owner(qapp):
    engine, component, root, helper = _create_scene()
    try:
        _invoke(root, "prewarmMenu")
        _pump(40)

        assert helper.calls
        assert helper.calls[-1][1] is root
        assert helper.calls[-1][0].metaObject().className() == "QQuickPopupWindow"
    finally:
        _dispose_scene(engine, component, root)
