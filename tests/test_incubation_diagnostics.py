# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Incubation diagnostic boundary regressions. 孵化诊断边界回归。"""

import pytest
from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlApplicationEngine

from prismqml.python.core import incubation


class _ScriptedController(incubation.PrismIncubationController):
    """Provide deterministic incubation counts. 提供确定性的孵化计数。"""

    def __init__(self, owner, counts, failure=None):
        self._counts = iter(counts)
        self._failure = failure
        self.budgets = []
        super().__init__(owner)
        self._timer.stop()

    def incubatingObjectCount(self):
        return next(self._counts)

    def incubateFor(self, budget_ms):
        self.budgets.append(budget_ms)
        if self._failure is not None:
            raise self._failure


def test_active_tick_logs_matching_begin_and_done_boundaries(monkeypatch, qapp):
    messages = []
    monkeypatch.setenv("PRISMQML_STARTUP_PROFILE_VERBOSE", "1")
    monkeypatch.setattr(
        incubation,
        "debug",
        lambda message, tag=None: messages.append((tag, message)),
    )
    owner = QObject()
    controller = _ScriptedController(owner, counts=[2, 1])

    controller._on_tick()

    assert controller.budgets == [5]
    assert len(messages) == 2
    assert all(tag == "Incubation" for tag, _ in messages)
    assert "tick begin sequence=1" in messages[0][1]
    assert "object_count_before=2" in messages[0][1]
    assert "budget_ms=5" in messages[0][1]
    assert "tick done sequence=1" in messages[1][1]
    assert "object_count_after=1" in messages[1][1]
    assert "timer_interval_ms=16" in messages[1][1]
    assert "elapsed_ms=" in messages[1][1]


def test_idle_tick_does_not_emit_active_diagnostics(monkeypatch, qapp):
    messages = []
    monkeypatch.setenv("PRISMQML_STARTUP_PROFILE_VERBOSE", "1")
    monkeypatch.setattr(
        incubation,
        "debug",
        lambda message, tag=None: messages.append((tag, message)),
    )
    owner = QObject()
    controller = _ScriptedController(owner, counts=[0, 0])

    controller._on_tick()

    assert controller.budgets == [5]
    assert messages == []
    assert controller._timer.interval() == 250


def test_new_incubation_work_promotes_idle_timer_immediately(qapp):
    owner = QObject()
    controller = incubation.PrismIncubationController(owner)

    assert controller._timer.interval() == controller._idle_interval
    controller.incubatingObjectCountChanged(1)

    assert controller._timer.isActive()
    assert controller._timer.interval() == controller._active_interval


def test_tick_failure_logs_boundary_and_reraises(monkeypatch, qapp):
    messages = []
    monkeypatch.setenv("PRISMQML_STARTUP_PROFILE_VERBOSE", "1")
    monkeypatch.setattr(
        incubation,
        "debug",
        lambda message, tag=None: messages.append(("debug", tag, message)),
    )
    monkeypatch.setattr(
        incubation,
        "exception",
        lambda message, tag=None: messages.append(("exception", tag, message)),
    )
    owner = QObject()
    controller = _ScriptedController(
        owner, counts=[1], failure=RuntimeError("incubation stopped")
    )

    with pytest.raises(RuntimeError, match="incubation stopped"):
        controller._on_tick()

    assert messages[0][0] == "debug"
    assert "tick begin sequence=1" in messages[0][2]
    assert messages[1][0:2] == ("exception", "Incubation")
    assert "tick failed sequence=1" in messages[1][2]
    assert "RuntimeError: incubation stopped" in messages[1][2]
    assert not any("tick done" in message for _, _, message in messages)


def test_installation_and_reuse_are_logged(monkeypatch, qapp):
    messages = []
    monkeypatch.setenv("PRISMQML_STARTUP_PROFILE_VERBOSE", "1")
    monkeypatch.setattr(
        incubation,
        "info",
        lambda message, tag=None: messages.append((tag, message)),
    )
    engine = QQmlApplicationEngine()

    controller = incubation.install_incubation_controller(engine)
    reused = incubation.install_incubation_controller(engine)
    controller._timer.stop()

    assert reused is controller
    assert messages[0][0] == "Incubation"
    assert "controller installed" in messages[0][1]
    assert "engine_type=QQmlApplicationEngine" in messages[0][1]
    assert messages[1][0] == "Incubation"
    assert "controller reused" in messages[1][1]


def test_default_installation_skips_windows_qt_6111(monkeypatch, qapp):
    messages = []
    monkeypatch.setattr(incubation.sys, "platform", "win32")
    monkeypatch.setattr(incubation, "qVersion", lambda: "6.11.1")
    monkeypatch.setattr(
        incubation,
        "warning",
        lambda message, tag=None: messages.append((tag, message)),
    )
    engine = QQmlApplicationEngine()

    installed = incubation.install_default_incubation_controller(engine)

    assert installed is None
    assert not isinstance(
        engine.incubationController(), incubation.PrismIncubationController
    )
    assert messages == [
        (
            "Incubation",
            "controller skipped qt_version=6.11.1 platform=win32 "
            "reason=QQmlConnections null VME method during sliced incubation",
        )
    ]


def test_default_installation_keeps_controller_on_other_platforms(
    monkeypatch, qapp
):
    monkeypatch.setattr(incubation.sys, "platform", "linux")
    monkeypatch.setattr(incubation, "qVersion", lambda: "6.11.1")
    engine = QQmlApplicationEngine()

    installed = incubation.install_default_incubation_controller(engine)

    try:
        assert isinstance(installed, incubation.PrismIncubationController)
        assert engine.incubationController() is installed
    finally:
        installed._timer.stop()


def test_detailed_logs_are_disabled_by_default(monkeypatch, qapp):
    messages = []
    monkeypatch.delenv("PRISMQML_STARTUP_PROFILE_VERBOSE", raising=False)
    monkeypatch.setattr(
        incubation,
        "debug",
        lambda message, tag=None: messages.append(("debug", tag, message)),
    )
    monkeypatch.setattr(
        incubation,
        "info",
        lambda message, tag=None: messages.append(("info", tag, message)),
    )
    owner = QObject()
    scripted = _ScriptedController(owner, counts=[1, 0])
    engine = QQmlApplicationEngine()

    scripted._on_tick()
    installed = incubation.install_incubation_controller(engine)
    installed._timer.stop()

    assert messages == []
