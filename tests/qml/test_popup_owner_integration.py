# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""PopupWindowCore owner repair integration. 弹层 owner 修复集成测试。"""

import sys
from pathlib import Path

import pytest
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


pytestmark = pytest.mark.skipif(
    sys.platform != "win32",
    reason="QQuickPopupWindow 原生 owner 修复只在 Windows 启用",
)

SCENE_URL = QUrl.fromLocalFile(__file__.replace(".py", ".qml"))
POPUP_SOURCE_PATH = (
    Path(__file__).resolve().parents[2]
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "utils"
    / "PopupWindowCore.qml"
)
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
    function acceptNativeClose() { nativeCloseAccepted() }
    function hideOwner() { hide() }

    signal nativeCloseAccepted()

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
        self.clear_calls = []
        self.release_calls = []

    @Slot("QVariant", "QVariant", result=bool)
    def ensurePopupWindowOwner(self, popup_window, owner_window) -> bool:
        self.calls.append((popup_window, owner_window))
        return True

    @Slot("QVariant", "QVariant", result=bool)
    def clearPopupWindowOwner(self, popup_window, owner_window) -> bool:
        self.clear_calls.append((popup_window, owner_window))
        return True

    @Slot("QVariant", "QVariant", result=bool)
    def releasePopupWindowCapture(self, popup_window, owner_window) -> bool:
        self.release_calls.append((popup_window, owner_window))
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


def test_cold_open_repairs_owner_without_deferred_work(qapp):
    engine, component, root, helper = _create_scene()
    try:
        _invoke(root, "openMenu")
        assert helper.calls
        assert all(owner is root for _, owner in helper.calls)
        assert all(
            popup.metaObject().className() == "QQuickPopupWindow"
            for popup, _ in helper.calls
        )
        _pump(20)
        assert helper.release_calls
        assert helper.release_calls[-1][1] is root
        assert (
            helper.release_calls[-1][0].metaObject().className()
            == "QQuickPopupWindow"
        )

        _invoke(root, "resetMenu")
        assert helper.clear_calls
        assert helper.clear_calls[-1][1] is root
        assert helper.clear_calls[-1][0].metaObject().className() == "QQuickPopupWindow"
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
        assert helper.clear_calls
        assert helper.release_calls == []
    finally:
        _dispose_scene(engine, component, root)


def test_accepted_native_close_clears_owner_before_host_teardown(qapp):
    engine, component, root, helper = _create_scene()
    try:
        _invoke(root, "openMenu")
        helper.clear_calls.clear()

        _invoke(root, "acceptNativeClose")

        assert helper.clear_calls
        assert helper.clear_calls[-1][1] is root
        assert helper.clear_calls[-1][0].metaObject().className() == "QQuickPopupWindow"
    finally:
        _dispose_scene(engine, component, root)


def test_hiding_owner_releases_open_qt_popup_owner(qapp):
    engine, component, root, helper = _create_scene()
    try:
        _invoke(root, "openMenu")
        helper.clear_calls.clear()

        _invoke(root, "hideOwner")
        _pump(20)

        assert helper.clear_calls
        assert helper.clear_calls[-1][1] is root
        assert helper.clear_calls[-1][0].metaObject().className() == "QQuickPopupWindow"
    finally:
        _dispose_scene(engine, component, root)


def test_owner_repair_uses_shared_event_queue_without_per_instance_timer():
    """Repair from onOpened without per-popup queued work. 从onOpened修复且不增加逐弹层排队对象。"""
    source = POPUP_SOURCE_PATH.read_text(encoding="utf-8")

    assert "popupStackingTimer" not in source
    assert "_scheduleQtPopupStackingRepair" not in source
    assert "onOpened:" in source
    assert "WindowHelper.ensurePopupWindowOwner(" in source
    assert "onAboutToHide:" in source
    assert "WindowHelper.clearPopupWindowOwner(" in source
    assert "WindowHelper.releasePopupWindowCapture(" in source
    assert "function onNativeCloseAccepted()" in source
