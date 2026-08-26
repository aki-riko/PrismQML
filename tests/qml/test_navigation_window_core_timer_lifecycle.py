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

import prismqml.python.runtime.window_services as window_services_module
from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "prismqml" / "PrismQML" / "NavigationWindowCore.qml"
SPLASH_TIMER_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "_internal"
    / "NavigationSplashTimer.qml"
)
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
        if (
            child.metaObject().className().startswith("QQmlTimer")
            or "Timer_QMLTYPE_" in child.metaObject().className()
            or child.metaObject().indexOfProperty("_minimumVisiblePhase") >= 0
        )
        and child.parent() is not None
        and child.parent().objectName() == "contentContainer"
    ]


def _running_timers(window: QObject) -> list[QObject]:
    return [timer for timer in _direct_timers(window) if timer.property("running")]


def _running_intervals(window: QObject) -> list[int]:
    return sorted(int(timer.property("interval")) for timer in _running_timers(window))


def _settled_object_count(window: QObject, timeout_ms: int = 800) -> int:
    """Wait until deferred window children stop changing. 等待延迟窗口子对象停止变化。"""
    assert _wait_for(lambda: window.property("_resizeHandlesReady") is True)
    elapsed = 0
    previous_count = -1
    stable_samples = 0
    while elapsed < timeout_ms:
        object_count = len(window.findChildren(QObject))
        if object_count == previous_count:
            stable_samples += 1
            if stable_samples >= 5:
                return object_count
        else:
            previous_count = object_count
            stable_samples = 0
        _pump()
        elapsed += 5
    raise AssertionError("NavigationWindowCore object tree did not settle")


def _create_scene(monkeypatch):
    engine = QQmlApplicationEngine()
    native_window = _FakeNativeWindow(engine)
    monkeypatch.setattr(
        window_services_module, "get_native_window_hook", lambda: native_window
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
        initial_object_count = _settled_object_count(window)
        assert initial_timer_count == 4
        assert _running_timers(window) == []

        assert QMetaObject.invokeMethod(window, "beginSplashWait")
        assert _running_intervals(window) == [5_000]

        assert QMetaObject.invokeMethod(window, "markSplashPageLoaded")
        assert _wait_for(lambda: len(_running_intervals(window)) == 1)
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
        settled_object_count = _settled_object_count(window)
        print(
            "NAVIGATION_WINDOW_TIMER",
            f"timers={initial_timer_count}/{settled_timer_count}",
            f"objects={initial_object_count}/{settled_object_count}",
            f"splash_elapsed={splash_elapsed}",
            f"mica_calls={len(mica_manager.calls)}",
        )

        assert settled_timer_count == 4
        assert settled_object_count == initial_object_count
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


def test_navigation_window_core_close_keeps_window_color_opaque(monkeypatch, qapp):
    """撤掉 Mica 背板后 windowColor 必须变回不透明, 否则整个窗口内部变半透明。

    windowColor 填充的是被遮罩层*内部*的 windowFrame 矩形(WindowsCoreFrame.qml:32),
    关闭圆环**裁得到**它 —— 所以它不该在关闭期间按住透明: 圆内要有正常底色, 圆外由
    遮罩裁掉。真机实测过按住透明的后果: Mica 一撤, 没人填充窗框, 整个内部透出后面的
    窗口。这条断言锁住"撤背板"与"保持不透明"必须同时成立。
    """
    engine, component, window, mica_manager, warnings = _create_scene(monkeypatch)
    try:
        window.setProperty("micaEnabled", True)
        window.setProperty("_nativeHookReady", True)
        assert _wait_for(lambda: window.property("_micaActive") is True)
        assert _wait_for(lambda: window.property("_micaBackdropReady") is True)
        # Mica on: transparent so the DWM material shows through.
        # Mica 开启时透明, 让 DWM 材质透出来。
        assert window.property("windowColor").alphaF() == 0.0

        # Dropping the backdrop for the close must also clear the translucency flag, or
        # windowColor stays transparent with nothing behind it.
        # 为关闭撤掉背板时必须同时清掉半透明标志, 否则 windowColor 仍透明而背后已无物。
        window.closeCollapseStateChanged.emit(True)
        assert window.property("_micaBackdropReady") is False
        assert window.property("_micaTransparent") is False
        assert window.property("windowColor").alphaF() == 1.0

        # Without Mica at all the base colour must stay opaque too.
        # 完全无 Mica 时底色同样必须不透明。
        window.setProperty("micaEnabled", False)
        assert _wait_for(lambda: window.property("_micaActive") is False)
        assert window.property("windowColor").alphaF() == 1.0

        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_navigation_window_core_close_collapse_drops_mica_backdrop(monkeypatch, qapp):
    """收紧期间必须把 DWM Mica 背板撤成 NONE, 否则被裁的外围照样是 Mica 材质。

    Mica 是 hwnd 级的 DWM 材质, 关闭圆环的 QML layer 遮罩到不了它 —— 与原生 DWM
    阴影同类。真机像素探针实测: QML 侧全透明什么都没画, 但判别点在 progress
    1.0 / 0.62 / 0.0 每一帧都是 #f0f4f9, 直到窗口真正消失才变成裸桌面色。
    见 scripts/manual/close_periphery_pixel_probe.py。
    """
    engine, component, window, mica_manager, warnings = _create_scene(monkeypatch)
    try:
        window.setProperty("micaEnabled", True)
        # The handler needs the native hook: the scene defaults it false, so opt in or
        # the assertion is vacuous. 处理器需要原生钩子: 场景默认假, 不显式打开断言是空的。
        window.setProperty("_nativeHookReady", True)
        assert _wait_for(lambda: window.property("_micaActive") is True)
        mica_manager.calls.clear()

        # Collapse start must disable the backdrop. 收紧开始必须关掉背板。
        window.closeCollapseStateChanged.emit(True)
        assert (False, False) in mica_manager.calls

        # A reapply landing mid-collapse would paint Mica back outside the circle,
        # so both the immediate apply and the scheduled one must be refused.
        # 收紧中途落地的重新应用会把 Mica 画回圆外, 故立即应用与排程都必须被拒。
        mica_manager.calls.clear()
        window.setProperty("_closeInProgress", True)
        assert QMetaObject.invokeMethod(window, "beginMicaReapply")
        # No timer may be armed and no apply may reach DWM while collapsing.
        # 收紧期间不得排程任何定时器, 也不得有 apply 落到 DWM。
        assert _running_timers(window) == []
        _pump(220)
        assert mica_manager.calls == []

        # Cancelling the close must put the backdrop back, or the window stays on
        # screen without Mica. 取消关闭必须装回背板, 否则窗口留在屏上却没了 Mica。
        window.setProperty("_closeInProgress", False)
        window.closeCollapseStateChanged.emit(False)
        assert any(enabled for enabled, _dark in mica_manager.calls)

        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_navigation_window_core_source_reuses_one_splash_timer():
    """Exclusive splash roles reuse one timer. 互斥的欢迎页角色复用一个计时器。"""
    source = SOURCE_PATH.read_text(encoding="utf-8")
    helper_source = SPLASH_TIMER_PATH.read_text(encoding="utf-8")

    assert source.count("\n    Timer {") == 0
    assert "NavigationSplashTimer {" in source
    assert "id: _splashTimer" in source
    assert "host: window" in source
    assert "id: _splashMinimumVisibleTimer" not in source
    assert "id: _splashTimeoutTimer" not in source
    assert "Qt.callLater(window._flushSplashDismissSchedule)" in source
    assert "id: _micaBackdropCommitTimer" in source
    assert "id: _micaReapplyTimer" in source
    assert "id: _micaLateReapplyTimer" in source
    assert "Timer {" in helper_source
    assert "required property var host" in helper_source
    assert "property bool _minimumVisiblePhase: false" in helper_source
    assert "Enums.duration.splashTimeout" in helper_source
    assert "host._scheduleSplashDismiss()" in helper_source
