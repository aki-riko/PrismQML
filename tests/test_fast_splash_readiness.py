# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Fast splash readiness polling regressions. 快速启动页就绪轮询回归。"""

from pathlib import Path

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

from prismqml import register_types
from prismqml.python.window import fast_splash as fast_splash_module
from prismqml.python.window.fast_splash import FastSplashController


ROOT = Path(__file__).resolve().parents[1]


class _PropertyObject:
    def __init__(self, **properties):
        self._properties = properties

    def property(self, name):
        return self._properties.get(name)


class _TimerStub:
    def __init__(self):
        self.stop_count = 0

    def stop(self):
        self.stop_count += 1


class _ClockStub:
    def __init__(self, now):
        self.now = now

    def monotonic(self):
        return self.now


def _source_window(*, page_ready: bool, busy: bool):
    page_loader = _PropertyObject(item=_PropertyObject() if page_ready else None)
    stack = _PropertyObject(
        _useSourceMode=True,
        busy=busy,
        currentWidget=page_loader,
    )
    return _PropertyObject(
        stackedWidget=stack,
        _pythonPageMode=False,
        lazyLoading=True,
        _startupPresentationReady=True,
        _splashInstance=None,
        _splashTimerObject=_PropertyObject(interval=5000, _timeoutInterval=5000),
    )


def _polling_controller(window, *, embedded: bool = False):
    controller = FastSplashController(None)
    controller._main_window = window
    controller._splash = object()
    controller._ready_timer = _TimerStub()
    controller._main_frame_count = 3
    controller._splash_frame_count = 1
    controller._page_ready_observed_frame = -1
    controller._handoff_done = False
    controller._embedded_handoff = embedded

    events = []
    controller._raise_owned_splash = lambda splash, main: events.append("raise")
    controller._start_reveal = lambda: events.append("reveal")
    controller._finish_embedded_handoff = lambda: events.append("embedded")
    return controller, events


def test_lazy_shell_does_not_reveal_before_first_page_is_ready():
    """A presentation-ready shell alone must not dismiss the splash."""
    window = _source_window(page_ready=False, busy=False)
    controller, events = _polling_controller(window)

    controller._poll_main_ready()

    assert events == []
    assert controller._page_ready_observed_frame == -1
    assert controller._ready_timer.stop_count == 0


def test_ready_page_does_not_reveal_while_initial_loading_indicator_is_busy():
    """A constructed page remains unready while its wait indicator exits."""
    window = _source_window(page_ready=True, busy=True)
    controller, events = _polling_controller(window)

    controller._poll_main_ready()

    assert events == []
    assert controller._page_ready_observed_frame == -1
    assert controller._ready_timer.stop_count == 0


def test_loading_exit_requires_one_more_submitted_frame_before_reveal():
    """Readiness must be followed by a newly submitted main-window frame."""
    window = _source_window(page_ready=True, busy=False)
    controller, events = _polling_controller(window)

    controller._poll_main_ready()
    assert controller._page_ready_observed_frame == 3
    assert events == []

    controller._poll_main_ready()
    assert events == []

    controller._main_frame_count = 4
    controller._poll_main_ready()

    assert events == ["raise", "reveal"]
    assert controller._ready_timer.stop_count == 1


def test_busy_state_return_resets_the_post_readiness_frame_gate():
    """A returning wait indicator invalidates an already observed ready frame."""
    window = _source_window(page_ready=True, busy=False)
    stack = window.property("stackedWidget")
    controller, events = _polling_controller(window)

    controller._poll_main_ready()
    assert controller._page_ready_observed_frame == 3

    controller._main_frame_count = 4
    stack._properties["busy"] = True
    controller._poll_main_ready()
    assert controller._page_ready_observed_frame == -1
    assert events == []

    controller._main_frame_count = 5
    stack._properties["busy"] = False
    controller._poll_main_ready()
    assert controller._page_ready_observed_frame == 5
    assert events == []

    controller._main_frame_count = 6
    controller._poll_main_ready()
    assert events == ["raise", "reveal"]


def test_failed_first_page_uses_splash_timeout_then_waits_one_more_frame(
    monkeypatch,
):
    """A terminal null Loader is bounded by the real splash timeout contract."""
    window = _source_window(page_ready=False, busy=False)
    window.property("_splashTimerObject")._properties["interval"] = 100
    controller, events = _polling_controller(window)
    clock = _ClockStub(100.0)
    warnings = []
    monkeypatch.setattr(fast_splash_module, "time", clock)
    monkeypatch.setattr(fast_splash_module, "warning", warnings.append)

    controller._poll_main_ready()
    assert controller._page_wait_started == 100.0
    assert controller._page_ready_observed_frame == -1
    assert events == []

    clock.now = 104.999
    controller._poll_main_ready()
    assert controller._page_ready_observed_frame == -1
    assert events == []
    assert warnings == []

    clock.now = 105.0
    controller._poll_main_ready()
    assert controller._page_ready_observed_frame == 3
    assert events == []
    assert len(warnings) == 1
    assert "首屏等待超时" in warnings[0]

    controller._poll_main_ready()
    assert events == []
    assert len(warnings) == 1

    controller._main_frame_count = 4
    controller._poll_main_ready()
    assert events == ["raise", "reveal"]
    assert controller._ready_timer.stop_count == 1
    assert len(warnings) == 1


def test_navigation_splash_timer_keeps_timeout_stable_in_minimum_visible_phase(
    qapp,
):
    """The minimum-visible phase must not overwrite the startup timeout."""
    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        b"""
import QtQuick
import "../prismqml/PrismQML/_internal"

Item {
    id: root

    function _scheduleSplashDismiss() {}

    NavigationSplashTimer {
        id: splashTimer

        objectName: "splashTimer"
        host: root
        _minimumVisibleInterval: 100
    }
}
""",
        QUrl.fromLocalFile(str(ROOT / "tests" / "fast-splash-readiness.qml")),
    )
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        qapp.processEvents()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    try:
        timer = root.findChild(QObject, "splashTimer")
        assert timer is not None
        assert timer.property("interval") == 5000
        assert timer.property("_timeoutInterval") == 5000

        assert timer.setProperty("_minimumVisiblePhase", True)
        assert timer.property("interval") == 100
        assert timer.property("_timeoutInterval") == 5000
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        qapp.processEvents()


def test_python_ready_indexes_ignore_source_busy_state():
    """Python readiness remains authoritative even when source-style busy is true."""
    page_loader = _PropertyObject(item=_PropertyObject())
    stack = _PropertyObject(
        _useSourceMode=True,
        busy=True,
        currentWidget=page_loader,
        currentIndex=0,
    )
    window = _PropertyObject(
        stackedWidget=stack,
        _pythonPageMode=True,
        _pythonReadyIndexes=[0],
    )

    assert FastSplashController._page_ready(window) is True


def test_python_page_never_uses_qml_source_timeout(monkeypatch):
    """An unready Python page cannot be released by elapsed QML splash time."""
    page = _PropertyObject()
    stack = _PropertyObject(
        _useSourceMode=False,
        busy=True,
        currentWidget=page,
        currentIndex=0,
    )
    window = _PropertyObject(
        stackedWidget=stack,
        _pythonPageMode=True,
        _pythonReadyIndexes=[],
        _startupPresentationReady=True,
        _splashInstance=None,
        _splashTimerObject=_PropertyObject(interval=5000, _timeoutInterval=5000),
    )
    controller, events = _polling_controller(window)
    controller._page_wait_started = 0.0
    warnings = []
    monkeypatch.setattr(fast_splash_module, "time", _ClockStub(60.0))
    monkeypatch.setattr(fast_splash_module, "warning", warnings.append)

    controller._poll_main_ready()

    assert FastSplashController._page_ready(window) is False
    assert controller._page_wait_expired() is False
    assert controller._page_ready_observed_frame == -1
    assert controller._page_wait_timed_out is False
    assert events == []
    assert warnings == []


def test_embedded_handoff_keeps_its_existing_frame_and_splash_gate():
    """The custom embedded fallback does not depend on page-stack readiness."""
    window = _PropertyObject(
        _splashInstance=None,
        _startupPresentationReady=False,
    )
    controller, events = _polling_controller(window, embedded=True)

    controller._main_frame_count = 0
    controller._poll_main_ready()
    assert events == []

    controller._main_frame_count = 1
    controller._poll_main_ready()
    assert events == []

    window._properties["_splashInstance"] = object()
    controller._poll_main_ready()
    assert events == []

    window._properties["_startupPresentationReady"] = True

    controller._poll_main_ready()

    assert events == ["embedded"]
    assert controller._ready_timer.stop_count == 1
