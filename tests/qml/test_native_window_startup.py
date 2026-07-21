# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""WindowsCore native hook startup contracts. WindowsCore 原生钩子启动合同。"""

from hashlib import sha256

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
    qInstallMessageHandler,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types
from prismqml.python.config.app_config import DEFAULT_APP_CONFIG
import prismqml.python.window as window_module


QML_LOAD_TIMEOUT_MS = 5000
STARTUP_SETTLE_MS = 400
POST_DESTROY_SETTLE_MS = 100
JS_NATIVE_WINDOW_SOURCE = b"""import QtQml
QtObject {
    property var finalizeOutcomes: []
    property bool throwAlways: false
    property bool returnUndefined: false
    property bool detachReturnsFalse: false
    property bool detachThrows: false
    property int finalizeCalls: 0
    property int detachCalls: 0
    function finalizeAttach(window) {
        finalizeCalls += 1
        if (throwAlways)
            throw new Error("native hook exploded")
        if (returnUndefined)
            return undefined
        if (finalizeCalls > finalizeOutcomes.length)
            return false
        return finalizeOutcomes[finalizeCalls - 1]
    }
    function detach(window) {
        detachCalls += 1
        if (detachThrows)
            throw new Error("native detach exploded")
        return !detachReturnsFalse
    }
}
"""


class _FakeNativeWindow(QObject):
    def __init__(self, finalize_outcomes):
        super().__init__()
        self.finalize_outcomes = list(finalize_outcomes)
        self.finalize_calls = 0
        self.detach_calls = 0

    @Slot(QObject, result=bool)
    def finalizeAttach(self, _window):
        self.finalize_calls += 1
        if not self.finalize_outcomes:
            return False
        outcome = self.finalize_outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    @Slot(QObject, result=bool)
    def detach(self, _window):
        self.detach_calls += 1
        return True


class _MissingFinalizeNativeWindow(QObject):
    def __init__(self):
        super().__init__()
        self.finalize_calls = 0
        self.detach_calls = 0

    @Slot(QObject, result=bool)
    def detach(self, _window):
        self.detach_calls += 1
        return True


class _MissingDetachNativeWindow(QObject):
    def __init__(self):
        super().__init__()
        self.finalize_calls = 0
        self.detach_calls = 0

    @Slot(QObject, result=bool)
    def finalizeAttach(self, _window):
        self.finalize_calls += 1
        return True


def _file_snapshot(path):
    if not path.exists():
        return None
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns, sha256(path.read_bytes()).hexdigest()


@pytest.fixture(autouse=True)
def _preserve_real_app_config():
    before = _file_snapshot(DEFAULT_APP_CONFIG)
    yield
    assert _file_snapshot(DEFAULT_APP_CONFIG) == before


def _pump(milliseconds: int) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_until(predicate, timeout_ms: int) -> None:
    if predicate():
        return
    loop = QEventLoop()
    poll = QTimer()
    poll.setInterval(1)
    poll.timeout.connect(lambda: loop.quit() if predicate() else None)
    poll.start()
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()
    assert predicate()


def _wait_component(component) -> None:
    if component.status() == QQmlComponent.Status.Loading:
        loop = QEventLoop()
        component.statusChanged.connect(
            lambda status: loop.quit()
            if status != QQmlComponent.Status.Loading
            else None
        )
        QTimer.singleShot(QML_LOAD_TIMEOUT_MS, loop.quit)
        loop.exec()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]


def _create_window(engine):
    component = QQmlComponent(engine)
    component.setData(
        b"""import PrismQML
WindowsCore {
    visible: false
    shadowMode: Enums.windowShadow.mode_none
    property int readyCount: 0
    onNativeHookReady: readyCount += 1
}
""",
        QUrl("inline:p7h-native-window-startup.qml"),
    )
    _wait_component(component)
    instance = component.create(engine.rootContext())
    assert instance is not None, [error.toString() for error in component.errors()]
    return component, instance


def _create_js_native_window(
    engine,
    *,
    outcomes=(),
    throw_always=False,
    return_undefined=False,
    detach_returns_false=False,
    detach_throws=False,
):
    component = QQmlComponent(engine)
    component.setData(
        JS_NATIVE_WINDOW_SOURCE,
        QUrl("inline:p7h-native-window-js-fake.qml"),
    )
    _wait_component(component)
    fake = component.create(engine.rootContext())
    assert fake is not None, [error.toString() for error in component.errors()]
    fake.setProperty("finalizeOutcomes", list(outcomes))
    fake.setProperty("throwAlways", throw_always)
    fake.setProperty("returnUndefined", return_undefined)
    fake.setProperty("detachReturnsFalse", detach_returns_false)
    fake.setProperty("detachThrows", detach_throws)
    return component, fake


def _fake_count(fake, python_name: str, qml_name: str) -> int:
    if fake is None:
        return 0
    value = getattr(fake, python_name, None)
    return int(value if value is not None else fake.property(qml_name))


def _wait_for_startup(fake, destroy_after_first_attempt: bool) -> None:
    if destroy_after_first_attempt:
        _wait_until(
            lambda: _fake_count(fake, "finalize_calls", "finalizeCalls") == 1,
            QML_LOAD_TIMEOUT_MS,
        )
        return
    _pump(STARTUP_SETTLE_MS)


def _startup_snapshot(instance, fake):
    return {
        "finalize_calls": _fake_count(fake, "finalize_calls", "finalizeCalls"),
        "ready_count": instance.property("readyCount"),
        "initialization_done": instance.property("_dwmInitializationDone"),
        "show_started": instance.property("_showAnimationStarted"),
        "show_start_count": instance.property("_showAnimationStartCount"),
        "opacity": instance.property("opacity"),
    }


def _delete_deferred(instance) -> None:
    if instance is None:
        return
    instance.deleteLater()
    QCoreApplication.sendPostedEvents(instance, QEvent.DeferredDelete)
    QCoreApplication.processEvents()


def _complete_snapshot(startup, fake) -> None:
    if startup is None:
        return
    startup["detach_calls"] = _fake_count(fake, "detach_calls", "detachCalls")
    startup["finalize_calls"] = _fake_count(
        fake, "finalize_calls", "finalizeCalls"
    )


def _destroy_window_for_snapshot(
    engine, instance, startup, fake, clear_native_before_destroy: bool
) -> None:
    if clear_native_before_destroy:
        engine.rootContext().setContextProperty("NativeWindow", None)
        QCoreApplication.processEvents()
    _delete_deferred(instance)
    _complete_snapshot(startup, fake)


def _create_engine(monkeypatch, fake, engine_warnings):
    monkeypatch.setattr(window_module, "get_native_window_hook", lambda: fake)
    engine = QQmlApplicationEngine()
    register_types(engine)
    if engine_warnings is not None:
        engine.warnings.connect(
            lambda errors: engine_warnings.extend(e.toString() for e in errors)
        )
    return engine


def _exercise(
    monkeypatch,
    fake,
    *,
    fake_factory=None,
    destroy_after_first_attempt: bool = False,
    clear_native_before_destroy: bool = False,
    engine_warnings=None,
):
    engine = _create_engine(monkeypatch, fake, engine_warnings)
    fake_component = None
    if fake_factory is not None:
        fake_component, fake = fake_factory(engine)
        engine.rootContext().setContextProperty("NativeWindow", fake)
    component = instance = None
    startup = None
    try:
        component, instance = _create_window(engine)
        _wait_for_startup(fake, destroy_after_first_attempt)
        startup = _startup_snapshot(instance, fake)
    finally:
        _destroy_window_for_snapshot(
            engine, instance, startup, fake, clear_native_before_destroy
        )
        component = fake_component = None
        _delete_deferred(engine)
        if destroy_after_first_attempt:
            _pump(POST_DESTROY_SETTLE_MS)
    return startup


def _exercise_with_messages(monkeypatch, fake, **kwargs):
    messages = []
    engine_warnings = []
    previous_handler = qInstallMessageHandler(
        lambda _mode, _context, message: messages.append(str(message))
    )
    try:
        result = _exercise(
            monkeypatch, fake, engine_warnings=engine_warnings, **kwargs
        )
    finally:
        qInstallMessageHandler(previous_handler)
    return result, messages, engine_warnings


def test_native_hook_success_emits_ready_and_shows_window(monkeypatch, qapp):
    result = _exercise(monkeypatch, _FakeNativeWindow([True]))

    assert result == {
        "finalize_calls": 1,
        "ready_count": 1,
        "initialization_done": True,
        "show_started": True,
        "show_start_count": 1,
        "opacity": 1.0,
        "detach_calls": 1,
    }


def test_prepare_before_show_finishes_native_hook_synchronously(monkeypatch, qapp):
    fake = _FakeNativeWindow([True])
    engine = _create_engine(monkeypatch, fake, [])
    component = instance = None
    try:
        component, instance = _create_window(engine)
        assert fake.finalize_calls == 0

        assert QMetaObject.invokeMethod(instance, "prepareBeforeShow")
        assert fake.finalize_calls == 1
        assert instance.property("readyCount") == 1
        assert instance.property("_dwmInitializationDone") is True
        assert instance.property("_showAnimationStartCount") == 1

        _pump(STARTUP_SETTLE_MS)
        assert fake.finalize_calls == 1
        assert instance.property("readyCount") == 1
        assert instance.property("_showAnimationStartCount") == 1
    finally:
        _delete_deferred(instance)
        component = None
        _delete_deferred(engine)


def test_native_hook_transient_failure_retries_once(monkeypatch, qapp):
    result = _exercise(monkeypatch, _FakeNativeWindow([False, True]))

    assert result == {
        "finalize_calls": 2,
        "ready_count": 1,
        "initialization_done": True,
        "show_started": True,
        "show_start_count": 1,
        "opacity": 1.0,
        "detach_calls": 1,
    }


def test_native_hook_persistent_failure_stops_after_one_retry(monkeypatch, qapp):
    result = _exercise(monkeypatch, _FakeNativeWindow([False, False]))

    assert result == {
        "finalize_calls": 2,
        "ready_count": 0,
        "initialization_done": True,
        "show_started": True,
        "show_start_count": 1,
        "opacity": 1.0,
        "detach_calls": 1,
    }


def test_native_hook_exception_does_not_block_show(monkeypatch, qapp):
    result = _exercise(
        monkeypatch,
        None,
        fake_factory=lambda engine: _create_js_native_window(
            engine, throw_always=True
        ),
    )

    assert result == {
        "finalize_calls": 2,
        "ready_count": 0,
        "initialization_done": True,
        "show_started": True,
        "show_start_count": 1,
        "opacity": 1.0,
        "detach_calls": 1,
    }


@pytest.mark.parametrize(
    ("outcomes", "return_undefined"),
    (([1, 1], False), (["true", "true"], False), ([], True)),
)
def test_native_hook_requires_literal_true(
    monkeypatch, qapp, outcomes, return_undefined
):
    result = _exercise(
        monkeypatch,
        None,
        fake_factory=lambda engine: _create_js_native_window(
            engine,
            outcomes=outcomes,
            return_undefined=return_undefined,
        ),
    )

    assert result == {
        "finalize_calls": 2,
        "ready_count": 0,
        "initialization_done": True,
        "show_started": True,
        "show_start_count": 1,
        "opacity": 1.0,
        "detach_calls": 1,
    }


def test_missing_finalize_method_does_not_publish_false_ready(monkeypatch, qapp):
    result = _exercise(monkeypatch, _MissingFinalizeNativeWindow())

    assert result == {
        "finalize_calls": 0,
        "ready_count": 0,
        "initialization_done": True,
        "show_started": True,
        "show_start_count": 1,
        "opacity": 1.0,
        "detach_calls": 1,
    }


def test_destroy_before_retry_cancels_future_attempt(monkeypatch, qapp):
    result = _exercise(
        monkeypatch,
        _FakeNativeWindow([False, True]),
        destroy_after_first_attempt=True,
    )

    assert result["finalize_calls"] == 1
    assert result["ready_count"] == 0
    assert result["initialization_done"] is True
    assert result["show_started"] is True
    assert result["show_start_count"] == 1
    assert result["detach_calls"] == 1


def test_missing_native_window_still_starts_show(monkeypatch, qapp):
    result = _exercise(monkeypatch, None)

    assert result == {
        "finalize_calls": 0,
        "ready_count": 0,
        "initialization_done": True,
        "show_started": True,
        "show_start_count": 1,
        "opacity": 1.0,
        "detach_calls": 0,
    }


@pytest.mark.parametrize(
    ("detach_behavior", "expected_warning"),
    (
        ("missing", "NativeWindow.detach failed during window destruction"),
        ("false", "NativeWindow.detach failed during window destruction"),
        ("throw", "NativeWindow.detach raised during window destruction"),
    ),
)
def test_native_detach_failures_do_not_break_destruction(
    monkeypatch, qapp, detach_behavior, expected_warning
):
    if detach_behavior == "missing":
        result, messages, engine_warnings = _exercise_with_messages(
            monkeypatch, _MissingDetachNativeWindow()
        )
        expected_detach_calls = 0
    else:
        result, messages, engine_warnings = _exercise_with_messages(
            monkeypatch,
            None,
            fake_factory=lambda engine: _create_js_native_window(
                engine,
                outcomes=[True],
                detach_returns_false=detach_behavior == "false",
                detach_throws=detach_behavior == "throw",
            ),
        )
        expected_detach_calls = 1

    assert result["finalize_calls"] == 1
    assert result["ready_count"] == 1
    assert result["show_start_count"] == 1
    assert result["opacity"] == 1.0
    assert result["detach_calls"] == expected_detach_calls
    assert any(expected_warning in message for message in messages)
    assert engine_warnings == []


def test_native_window_becoming_null_before_destruction_is_safe(
    monkeypatch, qapp
):
    result, messages, engine_warnings = _exercise_with_messages(
        monkeypatch,
        _FakeNativeWindow([True]),
        clear_native_before_destroy=True,
    )

    assert result["finalize_calls"] == 1
    assert result["ready_count"] == 1
    assert result["show_start_count"] == 1
    assert result["opacity"] == 1.0
    assert result["detach_calls"] == 0
    assert not any("NativeWindow.detach" in message for message in messages)
    assert engine_warnings == []
