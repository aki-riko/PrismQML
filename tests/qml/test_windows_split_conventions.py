# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""WindowsSplit loading and page-transfer contracts. 分栏窗口加载与页面转移合同。"""

from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QTimer,
    QUrl,
    Slot,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

import prismqml.python.window as window_module
from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
INTERNAL_PATH = ROOT / "prismqml" / "PrismQML" / "_internal"
SCENE_URL = QUrl.fromLocalFile(
    str(INTERNAL_PATH / "windows-split-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML
import "." as Internal

Internal.WindowsSplit {
    objectName: "splitWindow"
    width: 760
    height: 540
    visible: true
    shadowMode: Enums.windowShadow.mode_none

    Item {
        objectName: "pageA"
    }

    Item {
        objectName: "pageB"
    }
}
"""


class _FakeNativeWindow(QObject):
    @Slot(QObject, result=bool)
    def finalizeAttach(self, _window):
        return True

    @Slot(QObject, result=bool)
    def detach(self, _window):
        return True


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2400) -> bool:
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
        and not any(window is expected for expected in allowed)
    ]


def _create_scene(monkeypatch):
    engine = QQmlApplicationEngine()
    native_window = _FakeNativeWindow(engine)
    monkeypatch.setattr(
        window_module, "get_native_window_hook", lambda: native_window
    )
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
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


def _dispose_scene(engine, component, window) -> None:
    window.setVisible(False)
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def test_windows_split_loads_core_and_transfers_default_pages(monkeypatch, qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene(monkeypatch)
    try:
        assert _wait_for(lambda: window.property("stackedWidget") is not None)
        stack = window.property("stackedWidget")
        navigation = window.property("navigationView")
        page_a = window.findChild(QQuickItem, "pageA")
        page_b = window.findChild(QQuickItem, "pageB")
        assert stack is not None and navigation is not None
        assert page_a is not None and page_b is not None
        assert _wait_for(lambda: stack.property("count") == 2)
        container = stack.property("containerItem")
        assert page_a.parentItem() is container
        assert page_b.parentItem() is container
        assert page_a.isVisible() and not page_b.isVisible()
        assert window.property("titleBarLeftMargin") == window.property(
            "navCompactWidth"
        )

        window.setProperty("currentIndex", 1)
        assert _wait_for(lambda: stack.property("_displayIndex") == 1)
        assert stack.property("currentIndex") == 1
        assert not page_a.isVisible() and page_b.isVisible()
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
