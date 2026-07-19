# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Notification helper engine lifecycle regressions. 通知 helper 引擎生命周期回归。"""

import pytest
import shiboken6
from PySide6.QtCore import QtMsgType, qInstallMessageHandler
from PySide6.QtQml import QQmlApplicationEngine, qmlEngine

from prismqml.python.core import notification
from prismqml.python.core.engine import EngineManager
from prismqml.python.core.utils import register_types


_QT_FAILURE_TYPES = {
    QtMsgType.QtWarningMsg,
    QtMsgType.QtCriticalMsg,
    QtMsgType.QtFatalMsg,
}
_OFFSCREEN_FONT_WARNING = "QFontDatabase: Cannot find font directory"


def test_position_enum_matches_nine_grid_contract():
    """Python position values must match QML's row-major nine-grid. Python位置须匹配QML九宫格。"""
    assert {name: int(member) for name, member in notification.Position.__members__.items()} == {
        "TopLeft": 0,
        "Top": 1,
        "TopRight": 2,
        "Left": 3,
        "Center": 4,
        "Right": 5,
        "BottomLeft": 6,
        "Bottom": 7,
        "BottomRight": 8,
    }


def _release_engine(engine: QQmlApplicationEngine) -> None:
    """Release one engine and its registered bindings. 释放单个引擎及其注册绑定。"""
    if not shiboken6.isValid(engine):
        return
    EngineManager.set_engine(engine)
    EngineManager.reset()
    shiboken6.delete(engine)


@pytest.fixture
def qt_messages():
    """Capture Qt diagnostics and reject unknown warnings. 捕获并拒绝未知 Qt 警告。"""
    messages = []
    previous = qInstallMessageHandler(
        lambda mode, _context, message: messages.append((mode, str(message)))
    )
    yield messages
    qInstallMessageHandler(previous)
    failures = [
        message
        for mode, message in messages
        if mode in _QT_FAILURE_TYPES and _OFFSCREEN_FONT_WARNING not in message
    ]
    assert not failures


@pytest.fixture
def notification_engines(qapp, qt_messages):
    """Create two fully registered real engines. 创建两个完整注册的真实引擎。"""
    del qapp, qt_messages
    engine_a = QQmlApplicationEngine()
    engine_b = QQmlApplicationEngine()
    register_types(engine_a)
    register_types(engine_b)
    notification._helper = None
    EngineManager.reset()
    try:
        yield engine_a, engine_b
    finally:
        notification._helper = None
        _release_engine(engine_b)
        _release_engine(engine_a)


def test_helper_follows_current_engine(notification_engines):
    """Switching engines must replace the cached helper. 切换引擎必须替换缓存 helper。"""
    engine_a, engine_b = notification_engines
    EngineManager.set_engine(engine_a)
    helper_a = notification._get_helper()
    EngineManager.set_engine(engine_b)
    helper_b = notification._get_helper()

    assert helper_a is not None
    assert helper_b is not None
    assert helper_b is not helper_a
    assert helper_b.parent() is engine_b
    assert qmlEngine(helper_b) is engine_b


def test_helper_is_unavailable_after_engine_reset(notification_engines):
    """Reset must block cached and public dispatch. 重置后缓存与公开调用均必须不可用。"""
    engine_a, _engine_b = notification_engines
    EngineManager.set_engine(engine_a)
    assert notification._get_helper() is not None
    EngineManager.reset()

    helper_after_reset = notification._get_helper()
    public_result = notification.closeAllDesktopNotifications()

    assert helper_after_reset is None
    assert public_result is False


def test_helper_is_idempotent_for_same_engine(notification_engines):
    """One live engine must reuse one helper. 同一存活引擎必须复用同一 helper。"""
    engine_a, _engine_b = notification_engines
    EngineManager.set_engine(engine_a)
    helper_first = notification._get_helper()
    helper_second = notification._get_helper()

    assert helper_first is not None
    assert helper_second is helper_first
    assert helper_second.parent() is engine_a
    assert qmlEngine(helper_second) is engine_a


def test_helper_rebuilds_after_old_engine_is_destroyed(notification_engines):
    """Destroying the old engine must allow a clean rebuild. 旧引擎销毁后必须干净重建。"""
    engine_a, engine_b = notification_engines
    EngineManager.set_engine(engine_a)
    helper_first = notification._get_helper()
    assert helper_first is not None
    EngineManager.reset()
    shiboken6.delete(engine_a)
    assert not shiboken6.isValid(engine_a)
    assert not shiboken6.isValid(helper_first)
    EngineManager.set_engine(engine_b)

    helper_second = notification._get_helper()

    assert helper_second is not None
    assert helper_second is not helper_first
    assert helper_second.parent() is engine_b
    assert qmlEngine(helper_second) is engine_b


def test_python_helper_dispatches_desktop_options_atomically(monkeypatch):
    """Python helper must forward creation options in the same dispatch. Python入口须同次转发创建参数。"""
    calls = []

    def fake_invoke(method_name, *args):
        calls.append((method_name, args))
        return True

    monkeypatch.setattr(notification, "_invoke", fake_invoke)

    result = notification.showDesktopSuccess(
        "导出成功",
        "00:14\nC:/recordings/clip.mp4",
        duration=0,
        options={"closable": False, "progress": 0.25},
    )

    assert result is True
    assert calls == [
        (
            "desktopShow",
            (
                notification.Severity.SUCCESS,
                "导出成功",
                "00:14\nC:/recordings/clip.mp4",
                0,
                int(notification.Position.BottomRight),
                {"closable": False, "progress": 0.25},
            ),
        )
    ]
