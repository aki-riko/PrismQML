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


def test_async_qml_page_host_respects_shared_incubation_safety_gate(qapp, tmp_path):
    page_path = tmp_path / "SynchronousFallbackPage.qml"
    _write_page(page_path)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty(
        "PrismQmlAsynchronousPageLoaderEnabled", False
    )
    EngineManager.set_engine(engine)
    page = AsyncQmlPage(page_path)
    loader = page._qml_host.findChild(QObject, "asyncQmlPageContentLoader")
    assert loader is not None
    assert loader.property("asynchronous") is False

    page.start_loading()
    assert _pump_until(lambda: page.is_ready)
    EngineManager.reset()


def test_async_qml_page_reuses_compiled_host_per_engine(qapp, tmp_path):
    first_path = tmp_path / "FirstPage.qml"
    second_path = tmp_path / "SecondPage.qml"
    _write_page(first_path)
    _write_page(second_path)
    engine = QQmlApplicationEngine()
    EngineManager.set_engine(engine)
    first = AsyncQmlPage(first_path)
    second = AsyncQmlPage(second_path)

    assert first._qml_component is second._qml_component
    assert first._qml_host is not second._qml_host

    first.start_loading()
    second.start_loading()
    assert _pump_until(lambda: first.is_ready and second.is_ready)
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


def test_window_reveals_managed_async_page_without_regular_animation(qapp, tmp_path):
    """Python 懒加载首次显示仅由圆圈过渡负责。"""
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
        page_container = window._find_child_by_name("page_1")
        page_transition = stack.findChild(QObject, "lazyPageCircleTransition")
        circle_transition = stack.findChild(QObject, "qmlPageCircleTransition")
        assert page_container is not None
        assert page_transition is not None
        assert circle_transition is not None
        loading_seen = False
        animation_loading_states = []
        animation_finished = []
        circle_expansion_seen = []
        circle_phase_signals = []
        page_states = []

        def capture_page_state():
            page_states.append(
                (
                    bool(page_container.property("visible")),
                    float(page_container.property("opacity")),
                    float(page_container.property("y")),
                )
            )

        def on_loading_changed():
            nonlocal loading_seen
            loading_seen = loading_seen or bool(
                window._window.property("_pythonLoading")
            )

        def on_animation_started():
            animation_loading_states.append(
                bool(window._window.property("_pythonLoading"))
            )
            capture_page_state()

        window._window._pythonLoadingChanged.connect(on_loading_changed)
        stack.animationStarted.connect(on_animation_started)
        stack.animationFinished.connect(lambda: animation_finished.append(True))
        page_container.opacityChanged.connect(capture_page_state)
        page_container.yChanged.connect(capture_page_state)
        for signal_name in (
            "collapseStarted",
            "collapseFinished",
            "expandStarted",
            "expandFinished",
        ):
            getattr(page_transition, signal_name).connect(
                lambda name=signal_name: circle_phase_signals.append(name)
            )

        window._window.setProperty("currentIndex", 1)
        window._window.currentPageChanged.emit(1)

        assert _pump_until(
            lambda: circle_transition.property("running")
            and circle_transition.property("collapsing")
        )
        assert window._window.property("_pythonLoading") is False
        assert window._window.findChild(QObject, "loadingOverlay") is None
        assert stack.property("_displayIndex") == 0
        assert stack.property("_pendingLazySwitchIndex") == -1
        assert page_container.property("visible") is False

        assert _pump_until(
            lambda: window._window.findChild(QObject, "loadingOverlay") is not None
        )
        loading_overlay = window._window.findChild(QObject, "loadingOverlay")
        circle_frame = loading_overlay.findChild(QObject, "qmlPageCircleFrame")
        assert circle_frame is None
        circle_transition.runningChanged.connect(
            lambda: circle_expansion_seen.append(
                bool(circle_transition.property("running"))
                and not bool(circle_transition.property("collapsing"))
            )
        )
        assert page_transition.property("collapsed") is True
        assert circle_transition.property("running") is False
        assert window._window.property("_pythonLoading") is True
        assert animation_loading_states == []
        assert page_container.property("visible") is False

        assert _pump_until(
            lambda: 1 in window._pages and window._pages[1].is_ready
        )
        assert loading_seen
        assert _pump_until(lambda: any(circle_expansion_seen)), (
            f"signals={circle_expansion_seen} "
            f"page={page_transition.property('active')}/"
            f"{page_transition.property('collapsed')}/"
            f"{page_transition.property('_capturePending')}/"
            f"{page_transition.property('_overlayFrameStage')}/"
            f"{page_transition.property('_dissolving')}/"
            f"{page_transition.property('_mainFramePending')} "
            f"fallback={page_transition.property('_lastFallbackReason')} "
            f"circle={circle_transition.property('running')}/"
            f"{circle_transition.property('collapsing')}/"
            f"{circle_transition.property('progress')} "
            f"visible={page_container.property('visible')} "
            f"size={page_container.width()}x{page_container.height()} "
            f"loading={window._window.property('_pythonLoading')}"
        )
        assert _pump_until(lambda: loading_overlay.property("finishing"))
        assert animation_loading_states == []
        assert animation_finished == []
        capture_page_state()
        assert page_states[-1] == (True, 1.0, 0.0)
        assert _pump_until(
            lambda: window._window.findChild(QObject, "loadingOverlay") is None
        )
        assert _pump_until(
            lambda: page_transition.property("active") is False
        )
        assert circle_transition.property("collapsing") is False
        expected_phases = [
            "collapseStarted",
            "collapseFinished",
            "expandStarted",
            "expandFinished",
        ]
        assert circle_phase_signals == expected_phases

        for target_index in (0, 1):
            phase_count = len(circle_phase_signals)
            animation_started_count = len(animation_loading_states)
            animation_finished_count = len(animation_finished)
            assert window._window.property("_pythonLoading") is False
            window._window.setProperty("currentIndex", target_index)
            window._window.currentPageChanged.emit(target_index)
            assert _pump_until(
                lambda expected=animation_finished_count + 1:
                len(animation_finished) >= expected
            ), (
                f"circleSignals={circle_phase_signals} "
                f"animationStates={animation_loading_states} "
                f"rootIndex={window._window.property('currentIndex')} "
                f"stackIndex={stack.property('currentIndex')} "
                f"displayIndex={stack.property('_displayIndex')} "
                f"pendingIndex={stack.property('_pendingLazySwitchIndex')} "
                f"lazy={stack.property('lazyLoading')} "
                f"pythonMode={stack.property('_pythonPageMode')} "
                f"ready={stack.property('_pythonReadyIndexes').toVariant()} "
                f"target={stack.property('_pythonLazyTransitionTargetIndex')} "
                f"reveal={stack.property('_pythonLazyRevealRequested')} "
                f"active={page_transition.property('active')} "
                f"fallback={page_transition.property('_lastFallbackReason')}"
            )
            assert len(animation_loading_states) == animation_started_count + 1
            assert animation_loading_states[-1] is False
            assert len(circle_phase_signals) == phase_count
            assert page_transition.property("active") is False
            assert window._window.property("_pythonLoading") is False
            assert window._window.findChild(QObject, "loadingOverlay") is None

        window.setLazyLoading(False)
        assert _pump_until(
            lambda: window._window.property("lazyLoading") is False
            and stack.property("lazyLoading") is False
        )
        window.setLazyLoading(True)
        assert _pump_until(
            lambda: window._window.property("lazyLoading") is True
            and stack.property("lazyLoading") is True
        )
    finally:
        _dispose_window(window)


# ==================== 就绪兜底（2026-11-02）====================
# 背景：遮罩只由 page_ready / page_failed 释放。对「页面建出来了、既不报错
# 也永不就绪」此前没有任何超时，_pythonLoading 永远为 true、遮罩永久停留
# （下游 Kaleidos 2.0.2.284 用户报告「游戏库一直转圈、永远进不去」即此形态）。
# 下面两条用例分别钉住「永不就绪必须在兜底时长后被放行」与
# 「正常就绪不得被兜底提前打断」。


def test_page_ready_deadline_releases_never_ready_page(qapp, tmp_path):
    """页面永不就绪时，兜底必须放行遮罩门，而不是永久等待。"""
    page_path = tmp_path / "NeverReadyPage.qml"
    # gated=True 但 ready_delay_ms 极大：模拟「判据永不为 true」。
    _write_page(page_path, gated=True, ready_delay_ms=600_000)
    engine = QQmlApplicationEngine()
    EngineManager.set_engine(engine)
    controller = install_incubation_controller(engine)
    try:
        backend = _Backend()
        page = AsyncQmlPage(page_path, backend=backend, page_ready_deadline_ms=200)
        ready = []
        page.page_ready.connect(lambda: ready.append(True))

        page.start_loading()
        assert page.is_ready is False
        assert page._ready_deadline_timer is not None, "开始加载后必须布下兜底计时"

        assert _pump_until(lambda: page.is_ready, timeout_ms=3000), (
            "页面在兜底时长后仍未被放行，遮罩会永久停留"
        )
        assert ready == [True]
        assert page._ready_deadline_expired is True
        assert page.load_error == "", "兜底放行不是加载失败，不得置 load_error"
        # 兜底后宿主必须真的揭幕（visible 由 pageReady 驱动）。
        assert _pump_until(lambda: page._qml_item.property("pageReady") is True)
    finally:
        controller._timer.stop()
        EngineManager.reset()


def test_page_ready_deadline_does_not_disturb_normal_ready(qapp, tmp_path):
    """正常就绪路径必须撤销兜底计时，且只发一次 page_ready。"""
    page_path = tmp_path / "FastReadyPage.qml"
    _write_page(page_path, gated=True, ready_delay_ms=50)
    engine = QQmlApplicationEngine()
    EngineManager.set_engine(engine)
    controller = install_incubation_controller(engine)
    try:
        backend = _Backend()
        # 兜底时长远大于真实就绪时间：正常路径应当先落地。
        page = AsyncQmlPage(page_path, backend=backend, page_ready_deadline_ms=5000)
        ready = []
        page.page_ready.connect(lambda: ready.append(True))

        page.start_loading()
        assert _pump_until(lambda: page.is_ready, timeout_ms=3000)

        assert page._ready_deadline_expired is False, "正常就绪不得被标记成兜底放行"
        assert page._ready_deadline_timer is None, "正常就绪后必须撤销兜底计时"
        assert ready == [True], "page_ready 必须只发一次"
    finally:
        controller._timer.stop()
        EngineManager.reset()
