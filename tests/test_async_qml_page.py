# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""AsyncQmlPage runtime regressions. AsyncQmlPage 运行时回归。"""

from types import SimpleNamespace

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QObject,
    Property,
    QEventLoop,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem

from prismqml import AsyncQmlPage, Window, WindowType
from prismqml.python.core.engine import EngineManager
from prismqml.python.core.incubation import install_incubation_controller
from prismqml.python.window import AsyncQmlPage as WindowAsyncQmlPage


class _Backend(QObject):
    completed = Signal()

    @Property(str, constant=True)
    def marker(self):
        return "backend-ready"

    @Slot()
    def markLoaded(self):
        self.completed.emit()


def _pump_until(predicate, timeout_ms=3000):
    loop = QEventLoop()
    poll = QTimer()
    poll.setInterval(10)
    poll.timeout.connect(lambda: loop.quit() if predicate() else None)
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(loop.quit)
    poll.start()
    timeout.start(timeout_ms)
    loop.exec()
    poll.stop()
    return predicate()


def _write_page(path, *, gated=False, ready_delay_ms=100):
    ready_property = "property bool prismqmlAsyncReady: false" if gated else ""
    ready_timer = (
        f"Timer {{ interval: {ready_delay_ms}; running: true; "
        "onTriggered: parent.prismqmlAsyncReady = true }"
        if gated
        else ""
    )
    path.write_text(
        f"""
import QtQuick
Item {{
    property var backend: null
    {ready_property}
    property string marker: backend ? backend.marker : ""
    Component.onCompleted: backend.markLoaded()
    {ready_timer}
}}
""",
        encoding="utf-8",
    )


def _plain_page():
    item = QQuickItem()
    item.setWidth(640)
    item.setHeight(480)
    return SimpleNamespace(_qml_item=item)


def _dispose_window(window):
    qml_window = window._window
    if qml_window is not None and shiboken6.isValid(qml_window):
        qml_window.setProperty("visible", False)
        qml_window.deleteLater()
        QCoreApplication.sendPostedEvents(qml_window, QEvent.DeferredDelete)
    window._window = None
    QCoreApplication.processEvents()
    EngineManager.reset()


def test_async_qml_page_injects_backend_before_completed(qapp, tmp_path):
    assert WindowAsyncQmlPage is AsyncQmlPage
    page_path = tmp_path / "TargetPage.qml"
    _write_page(page_path)
    engine = QQmlApplicationEngine()
    EngineManager.set_engine(engine)
    controller = install_incubation_controller(engine)
    backend = _Backend()
    completed = []
    ready = []
    backend.completed.connect(lambda: completed.append(True))

    page = AsyncQmlPage(page_path, backend=backend)
    page.page_ready.connect(lambda: ready.append(True))
    host = page._qml_item
    assert host.property("pageReady") is False

    page.start_loading()
    page.start_loading()

    assert _pump_until(lambda: page.is_ready)
    assert completed == [True]
    assert ready == [True]
    assert host.property("pageReady") is True
    assert page._qml_item is host.property("contentItem")
    assert page._qml_item.property("marker") == "backend-ready"
    assert page.load_error == ""

    controller._timer.stop()
    EngineManager.reset()


def test_async_qml_page_waits_for_optional_target_ready_gate(qapp, tmp_path):
    page_path = tmp_path / "GatedPage.qml"
    _write_page(page_path, gated=True)
    engine = QQmlApplicationEngine()
    EngineManager.set_engine(engine)
    controller = install_incubation_controller(engine)
    backend = _Backend()
    completed = []
    backend.completed.connect(lambda: completed.append(True))

    page = AsyncQmlPage(page_path, backend=backend)
    host = page._qml_item
    page.start_loading()

    assert _pump_until(lambda: completed == [True])
    assert page.is_ready is False
    assert host.property("pageReady") is False
    assert _pump_until(lambda: page.is_ready)
    assert host.property("pageReady") is True

    controller._timer.stop()
    EngineManager.reset()


def test_async_qml_page_reports_real_loader_failure(qapp, tmp_path):
    missing_path = tmp_path / "MissingPage.qml"
    engine = QQmlApplicationEngine()
    EngineManager.set_engine(engine)
    controller = install_incubation_controller(engine)
    page = AsyncQmlPage(missing_path)
    failures = []
    page.page_failed.connect(failures.append)

    page.start_loading()

    assert _pump_until(lambda: bool(failures))
    assert page.is_ready is False
    assert missing_path.as_posix() in page.load_error.replace("\\", "/")

    controller._timer.stop()
    EngineManager.reset()


def test_window_animates_managed_async_page_after_loading_finishes(qapp, tmp_path):
    """Python 懒加载完成后必须播放目标页入场动画，而不是直接显现。"""
    page_path = tmp_path / "DelayedTargetPage.qml"
    _write_page(page_path, gated=True, ready_delay_ms=500)

    class IsolatedWindow(Window):
        _GENERATED_QML_CACHE_DIR = tmp_path / "window-qml"

    window = IsolatedWindow(window_type=WindowType.BAR)
    window.setSplashEnabled(False)
    window.setLazyLoading(True)
    window.addPage(_plain_page, "Home", "Home")
    window.addPage(lambda: AsyncQmlPage(page_path), "Library", "Library")

    try:
        window.show()
        assert _pump_until(
            lambda: window._window.property("stackedWidget") is not None
        )
        stack = window._window.property("stackedWidget")
        loading_seen = False
        animation_after_loading = []

        def on_loading_changed():
            nonlocal loading_seen
            loading_seen = loading_seen or bool(
                window._window.property("_pythonLoading")
            )

        def on_animation_started():
            animation_after_loading.append(
                loading_seen and not window._window.property("_pythonLoading")
            )

        window._window._pythonLoadingChanged.connect(on_loading_changed)
        stack.animationStarted.connect(on_animation_started)

        window._window.setProperty("currentIndex", 1)
        window._window.currentPageChanged.emit(1)

        assert _pump_until(
            lambda: 1 in window._pages and window._pages[1].is_ready
        )
        assert loading_seen
        assert any(animation_after_loading), animation_after_loading
    finally:
        _dispose_window(window)
