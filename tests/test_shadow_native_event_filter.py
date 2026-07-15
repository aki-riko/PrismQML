# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""DWM native event filter exception boundaries. DWM 原生事件过滤器异常边界。"""

import logging
from types import SimpleNamespace

import pytest
import shiboken6
from PySide6.QtCore import QByteArray, QCoreApplication, QEvent
from PySide6.QtGui import QWindow

import prismqml.python.core.shadow as shadow


def _raising_flush(error):
    def fail():
        raise error

    return fail


def _filter_with_flush(flush):
    event_filter = shadow.DwmSyncFilter()
    message_class = SimpleNamespace(
        from_address=lambda _address: SimpleNamespace(message=event_filter.WM_SIZE)
    )
    event_filter._get_msg_class = lambda: message_class
    event_filter._dwmapi = SimpleNamespace(DwmFlush=flush)
    return event_filter


def _native_shadow_manager(monkeypatch):
    monkeypatch.setattr(shadow.ShadowManager, "_instance", None)
    manager = shadow.ShadowManager()
    manager._mode = shadow.ShadowMode.NATIVE
    return manager


def _deleted_window(qapp):
    window = QWindow()
    window.deleteLater()
    QCoreApplication.sendPostedEvents(window, QEvent.DeferredDelete)
    qapp.processEvents()
    assert not shiboken6.isValid(window)
    return window


class _ProcessControlWindow:
    def __init__(self, error):
        self._error = error

    def winId(self):
        raise self._error


class _InstallApp:
    def __init__(self, outcomes):
        self._outcomes = iter(outcomes)
        self.filters = []

    def installNativeEventFilter(self, event_filter):
        self.filters.append(event_filter)
        outcome = next(self._outcomes)
        if outcome is not None:
            raise outcome


def _prepare_install(monkeypatch, outcomes):
    app = _InstallApp(outcomes)
    monkeypatch.setattr(shadow.sys, "platform", "win32")
    monkeypatch.setattr(
        shadow,
        "QApplication",
        SimpleNamespace(instance=lambda: app),
    )
    monkeypatch.setattr(shadow, "DwmSyncFilter", type("FakeFilter", (), {}))
    monkeypatch.setattr(shadow, "_dwm_sync_filter", None)
    return app


def _prepare_recording_install(monkeypatch):
    events = []
    candidate = object()

    class RecordingApp:
        def installNativeEventFilter(self, event_filter):
            events.append(("install", event_filter))
            assert shadow._dwm_sync_filter is None

    def construct_filter():
        events.append("construct")
        return candidate

    def record_info(message):
        assert shadow._dwm_sync_filter is candidate
        events.append(("info", message))

    monkeypatch.setattr(shadow.sys, "platform", "win32")
    monkeypatch.setattr(
        shadow,
        "QApplication",
        SimpleNamespace(instance=RecordingApp),
    )
    monkeypatch.setattr(shadow, "DwmSyncFilter", construct_filter)
    monkeypatch.setattr(shadow, "info", record_info)
    monkeypatch.setattr(shadow, "_dwm_sync_filter", None)
    return candidate, events


def test_native_event_filter_logs_runtime_error_and_keeps_dispatching(monkeypatch):
    messages = []
    monkeypatch.setattr(shadow, "exception", messages.append)
    event_filter = _filter_with_flush(
        _raising_flush(RuntimeError("DwmFlush failed"))
    )

    result = event_filter.nativeEventFilter(QByteArray(), 1)

    assert result == (False, 0)
    assert messages == [
        "DwmSyncFilter nativeEventFilter error intercepted: "
        "RuntimeError: DwmFlush failed"
    ]


@pytest.mark.parametrize("error_type", (KeyboardInterrupt, SystemExit))
def test_native_event_filter_does_not_swallow_process_control(error_type):
    event_filter = _filter_with_flush(_raising_flush(error_type("stop")))

    with pytest.raises(error_type, match="stop"):
        event_filter.nativeEventFilter(QByteArray(), 1)


def test_install_failure_logs_traceback_state_and_allows_retry(monkeypatch):
    messages = []
    app = _prepare_install(
        monkeypatch,
        (RuntimeError("native filter rejected"), None),
    )
    monkeypatch.setattr(shadow, "exception", messages.append)

    assert shadow.installDwmSyncFilter() is False
    assert shadow._dwm_sync_filter is None
    assert shadow.installDwmSyncFilter() is True

    assert len(app.filters) == 2
    assert shadow._dwm_sync_filter is app.filters[-1]
    assert messages == [
        "DWM sync filter installation failed: "
        "RuntimeError: native filter rejected"
    ]


def test_install_requires_application_before_constructing_filter(monkeypatch):
    constructed = []
    warnings = []
    monkeypatch.setattr(shadow.sys, "platform", "win32")
    monkeypatch.setattr(
        shadow,
        "QApplication",
        SimpleNamespace(instance=lambda: None),
    )
    monkeypatch.setattr(shadow, "DwmSyncFilter", lambda: constructed.append(True))
    monkeypatch.setattr(shadow, "warning", warnings.append)
    monkeypatch.setattr(shadow, "_dwm_sync_filter", None)

    assert shadow.installDwmSyncFilter() is False
    assert constructed == []
    assert warnings == ["QApplication未创建"]


def test_install_success_is_idempotent(monkeypatch):
    app = _prepare_install(monkeypatch, (None,))

    assert shadow.installDwmSyncFilter() is True
    installed_filter = shadow._dwm_sync_filter
    assert shadow.installDwmSyncFilter() is True

    assert app.filters == [installed_filter]


def test_install_publishes_only_after_native_registration_succeeds(monkeypatch):
    candidate, events = _prepare_recording_install(monkeypatch)

    assert shadow.installDwmSyncFilter() is True

    assert shadow._dwm_sync_filter is candidate
    assert events == [
        "construct",
        ("install", candidate),
        ("info", "DWM同步过滤器已安装"),
    ]


def test_constructor_failure_logs_traceback_without_caching(monkeypatch):
    messages = []
    app = _prepare_install(monkeypatch, ())

    def fail_construction():
        raise RuntimeError("filter construction failed")

    monkeypatch.setattr(shadow, "DwmSyncFilter", fail_construction)
    monkeypatch.setattr(shadow, "exception", messages.append)

    assert shadow.installDwmSyncFilter() is False
    assert shadow._dwm_sync_filter is None
    assert app.filters == []
    assert messages == [
        "DWM sync filter installation failed: "
        "RuntimeError: filter construction failed"
    ]


@pytest.mark.parametrize("error_type", (KeyboardInterrupt, SystemExit))
def test_install_failure_does_not_swallow_or_cache_process_control(
    monkeypatch,
    error_type,
):
    _prepare_install(monkeypatch, (error_type("stop"),))

    with pytest.raises(error_type, match="stop"):
        shadow.installDwmSyncFilter()

    assert shadow._dwm_sync_filter is None


@pytest.mark.parametrize("error_type", (KeyboardInterrupt, SystemExit))
def test_constructor_does_not_swallow_or_cache_process_control(
    monkeypatch,
    error_type,
):
    app = _prepare_install(monkeypatch, ())

    def fail_construction():
        raise error_type("stop")

    monkeypatch.setattr(shadow, "DwmSyncFilter", fail_construction)

    with pytest.raises(error_type, match="stop"):
        shadow.installDwmSyncFilter()

    assert shadow._dwm_sync_filter is None
    assert app.filters == []


@pytest.mark.parametrize(
    "method_name",
    ("enableShadowForWindow", "disableShadowForWindow"),
)
def test_window_shadow_boundary_logs_deleted_qwindow_traceback(
    monkeypatch, qapp, caplog, method_name
):
    manager = _native_shadow_manager(monkeypatch)
    window = _deleted_window(qapp)

    with caplog.at_level(logging.ERROR, logger="PrismQML"):
        assert getattr(manager, method_name)(window) is False

    records = [
        record for record in caplog.records
        if f"ShadowManager.{method_name} failed" in record.getMessage()
    ]
    assert len(records) == 1
    assert records[0].exc_info is not None
    assert records[0].exc_info[0] is RuntimeError
    assert "Traceback (most recent call last):" in caplog.text
    assert "window.winId()" in caplog.text
    assert "already deleted" in caplog.text


@pytest.mark.parametrize(
    "method_name",
    ("enableShadowForWindow", "disableShadowForWindow"),
)
@pytest.mark.parametrize("error_type", (KeyboardInterrupt, SystemExit))
def test_window_shadow_boundary_propagates_process_control(
    monkeypatch, method_name, error_type
):
    manager = _native_shadow_manager(monkeypatch)
    window = _ProcessControlWindow(error_type("stop"))

    with pytest.raises(error_type, match="stop"):
        getattr(manager, method_name)(window)
