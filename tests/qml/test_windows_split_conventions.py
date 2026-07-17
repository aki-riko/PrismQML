# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""WindowsSplit loading and page-transfer contracts. 分栏窗口加载与页面转移合同。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    Property,
    QTimer,
    QUrl,
    Slot,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

import prismqml.python.window as window_module
from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
INTERNAL_PATH = ROOT / "prismqml" / "PrismQML" / "_internal"
SOURCE_PATH = INTERNAL_PATH / "WindowsSplit.qml"
FILLED_SOURCE_PATH = INTERNAL_PATH / "WindowsFilled.qml"
METRICS_PATH = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(INTERNAL_PATH / "windows-split-conventions.qml")
)
SPLIT_SCENE_SOURCE = b"""
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
FILLED_SCENE_SOURCE = b"""
import QtQuick
import PrismQML
import "." as Internal

Internal.WindowsFilled {
    objectName: "filledWindow"
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


class _UnavailableMicaManager(QObject):
    @Property(bool, constant=True)
    def isMicaSupported(self):
        return False


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


def _create_scene(monkeypatch, scene_source):
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
    mica_manager = _UnavailableMicaManager(engine)
    engine.rootContext().setContextProperty("MicaManager", mica_manager)
    component = QQmlComponent(engine)
    component.setData(scene_source, SCENE_URL)
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


def _assert_page_transfer(window):
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

    window.setProperty("currentIndex", 1)
    assert _wait_for(lambda: stack.property("_displayIndex") == 1)
    assert stack.property("currentIndex") == 1
    assert not page_a.isVisible() and page_b.isVisible()


def _exercise_page_transfer(
    monkeypatch,
    scene_source,
    check_compact_margin=False,
    expected_warning="",
):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene(monkeypatch, scene_source)
    try:
        _assert_page_transfer(window)
        if check_compact_margin:
            assert window.property("titleBarLeftMargin") == window.property(
                "navCompactWidth"
            )
        if expected_warning:
            assert len(warnings) == 1
            assert expected_warning in warnings[0]
        else:
            assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_windows_split_loads_core_and_transfers_default_pages(monkeypatch, qapp):
    _exercise_page_transfer(monkeypatch, SPLIT_SCENE_SOURCE, True)


def test_windows_filled_loads_core_and_transfers_default_pages(monkeypatch, qapp):
    _exercise_page_transfer(monkeypatch, FILLED_SCENE_SOURCE)


def test_windows_split_source_conventions_and_startup_delay_token():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    assert "interval: Enums.window.splitStartupDelayMs" in source
    assert "interval: 50" not in source
    metrics = METRICS_PATH.read_text(encoding="utf-8")
    assert "readonly property int splitStartupDelayMs: 50" in metrics


def test_windows_filled_source_conventions_and_stack_binding():
    source = FILLED_SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(FILLED_SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    assert "stackedWidget: stack" not in source
    assert "window.stackedWidget = item.stackAlias" in source
    assert "interval: Enums.window.splitStartupDelayMs" in source
