# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""DWM native event filter exception boundaries. DWM 原生事件过滤器异常边界。"""

from types import SimpleNamespace

import pytest
from PySide6.QtCore import QByteArray

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
