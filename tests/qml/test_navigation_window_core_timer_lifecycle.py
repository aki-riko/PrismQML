# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Navigation-window timer lifecycle regressions. 导航窗口计时器生命周期回归。"""

from __future__ import annotations

from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    Property,
    QTimer,
    QUrl,
    Slot,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickWindow

import prismqml.python.window as window_module
from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "prismqml" / "PrismQML" / "NavigationWindowCore.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "navigation-window-core-timer-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

NavigationWindowCore {
    id: window

    property int splashFinishCount: 0
    property double splashRequestedAtMs: 0
    property double splashFinishedAtMs: 0

    function beginSplashWait() {
        splashStub.loaded = false
        _splashInstance = splashStub
        _splashVisibleSinceMs = Date.now()
        splashRequestedAtMs = Date.now()
        _dismissSplashWhenReady(stackStub)
    }
    function markSplashPageLoaded() {
        splashStub.loaded = true
        stackStub.pageLoaded(stackStub.currentIndex)
    }
    function beginMicaReapply() {
        _nativeHookReady = false
        micaEnabled = true
        _nativeHookReady = true
        _scheduleMicaReapply("timer-baseline")
    }

    width: 320
    height: 180
    visible: false
    shadowMode: Enums.windowShadow.mode_none
    splashEnabled: false
    splashMinimumVisibleDuration: 160
    micaEnabled: false

    QtObject {
        id: splashStub

        property bool loaded: false

        function finish() {
            window.splashFinishCount += 1
            window.splashFinishedAtMs = Date.now()
        }
    }

    QtObject {
        id: stackStub

        property int currentIndex: 0

        signal pageLoaded(int index)

        function _isPageLoaded(index) { return splashStub.loaded }
    }
}
"""


class _AvailableMicaManager(QObject):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.calls: list[tuple[bool, bool]] = []

    @Property(bool, constant=True)
    def isMicaSupported(self) -> bool:
        return True

    @Slot(QObject, bool, bool, result=bool)
    def setMicaEffect(self, _window: QObject, enabled: bool, dark: bool) -> bool:
        self.calls.append((enabled, dark))
        return True


class _FakeNativeWindow(QObject):
    @Slot(QObject, result=bool)
    def finalizeAttach(self, _window: QObject) -> bool:
        return True

    @Slot(QObject, result=bool)
    def detach(self, _window: QObject) -> bool:
        return True


def _pump(milliseconds: int = 5) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 5
    return predicate()


def _direct_timers(window: QObject) -> list[QObject]:
    return [
        child
        for child in window.findChildren(QObject)
        if child.metaObject().className().startswith("QQmlTimer")
        and child.parent() is not None
        and child.parent().objectName() == "contentContainer"
    ]


def _running_timers(window: QObject) -> list[QObject]:
    return [timer for timer in _direct_timers(window) if timer.property("running")]


def _running_intervals(window: QObject) -> list[int]:
    return sorted(int(timer.property("interval")) for timer in _running_timers(window))


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
    mica_manager = _AvailableMicaManager(engine)
    engine.rootContext().setContextProperty("MicaManager", mica_manager)
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
    return engine, component, window, mica_manager, warnings


def _dispose_scene(qapp, engine, component, window) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def test_navigation_window_core_timer_lifecycle_baseline(monkeypatch, qapp):
    """Four timers preserve serial splash and concurrent Mica roles. 四个计时器保持欢迎页串行与 Mica 并行角色。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, mica_manager, warnings = _create_scene(monkeypatch)
    try:
        initial_timer_count = len(_direct_timers(window))
        assert _wait_for(lambda: len(window.findChildren(QObject)) == 73)
        initial_object_count = len(window.findChildren(QObject))
        assert initial_timer_count == 4
        assert _running_timers(window) == []

        assert QMetaObject.invokeMethod(window, "beginSplashWait")
        assert _running_intervals(window) == [5_000]

        assert QMetaObject.invokeMethod(window, "markSplashPageLoaded")
        splash_intervals = _running_intervals(window)
        assert len(splash_intervals) == 1
        assert 16 <= splash_intervals[0] <= 160
        assert _wait_for(lambda: window.property("splashFinishCount") == 1)
        splash_elapsed = (
            window.property("splashFinishedAtMs")
            - window.property("splashRequestedAtMs")
        )
        assert splash_elapsed >= 140
        assert _running_timers(window) == []

        mica_manager.calls.clear()
        assert QMetaObject.invokeMethod(window, "beginMicaReapply")
        assert _running_intervals(window) == [16, 180]
        assert _wait_for(
            lambda: len(mica_manager.calls) >= 1
            and _running_intervals(window) == [16, 180]
        )
        assert _wait_for(lambda: len(mica_manager.calls) == 2)
        assert _wait_for(lambda: window.property("_micaBackdropReady") is True)
        assert _wait_for(lambda: _running_timers(window) == [])

        settled_timer_count = len(_direct_timers(window))
        assert _wait_for(lambda: len(window.findChildren(QObject)) == 73)
        settled_object_count = len(window.findChildren(QObject))
        print(
            "NAVIGATION_WINDOW_TIMER",
            f"timers={initial_timer_count}/{settled_timer_count}",
            f"objects={initial_object_count}/{settled_object_count}",
            f"splash_elapsed={splash_elapsed}",
            f"mica_calls={len(mica_manager.calls)}",
        )

        assert settled_timer_count == 4
        assert (initial_object_count, settled_object_count) == (73, 73)
        assert mica_manager.calls == [(True, False), (True, False)]
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)
        assert [
            candidate
            for candidate in QGuiApplication.topLevelWindows()
            if candidate.isVisible()
            and not any(candidate is existing for existing in windows_before)
        ] == []


def test_navigation_window_core_source_reuses_one_splash_timer():
    """Exclusive splash roles reuse one timer. 互斥的欢迎页角色复用一个计时器。"""
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert source.count("Timer {") == 4
    assert "id: _splashTimer" in source
    assert "id: _splashMinimumVisibleTimer" not in source
    assert "id: _splashTimeoutTimer" not in source
    assert "id: _micaBackdropCommitTimer" in source
    assert "id: _micaReapplyTimer" in source
    assert "id: _micaLateReapplyTimer" in source
