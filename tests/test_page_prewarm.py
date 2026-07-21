# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Page startup guard and prewarm scheduling regressions. 页面启动保护与预热调度回归。"""

from __future__ import annotations

from types import SimpleNamespace

from prismqml.python.window import _page_manager
from prismqml.python.window._page_prewarm import initialize_page_prewarm_state


class _TimerQueue:
    def __init__(self):
        self.calls = []

    def single_shot(self, delay, callback):
        self.calls.append((delay, callback))

    def run_next(self):
        _delay, callback = self.calls.pop(0)
        callback()


class _Manager(_page_manager.PageManagerMixin):
    def __init__(self):
        self._lazy_loading = True
        self._current_index = 0
        self._pages = {}
        self._nav_items = [object(), object(), object()]
        self._bottom_nav_items = []
        self._window = object()
        self.created = []
        initialize_page_prewarm_state(self)

    def _create_page(self, index):
        self.created.append(index)
        self._pages[index] = SimpleNamespace(_prismqml_async_page=False)


class _GuardedCreateManager(_Manager):
    def _create_page(self, index):
        return _page_manager.PageManagerMixin._create_page(self, index)


def _install_timer(monkeypatch):
    timers = _TimerQueue()
    monkeypatch.setattr(
        "prismqml.python.window._page_prewarm.QTimer",
        SimpleNamespace(singleShot=timers.single_shot),
    )
    return timers


def test_startup_guard_rejects_noncurrent_forced_page_creation(monkeypatch):
    warnings = []
    manager = _Manager()
    manager._begin_startup_page_guard()
    monkeypatch.setattr(_page_manager, "warning", warnings.append)

    created = manager._ensure_page_created(1)

    assert created is False
    assert manager.created == []
    assert len(warnings) == 1
    assert "prewarmPage" in warnings[0]


def test_startup_guard_also_rejects_direct_internal_page_creation(monkeypatch):
    warnings = []
    manager = _GuardedCreateManager()
    manager._begin_startup_page_guard()
    monkeypatch.setattr(_page_manager, "warning", warnings.append)

    created = manager._create_page(1)

    assert created is False
    assert manager.created == []
    assert len(warnings) == 1


def test_startup_guard_allows_current_page_and_finishes_when_ready():
    manager = _Manager()
    manager._begin_startup_page_guard()

    created = manager._ensure_page_created(0)
    manager._complete_startup_page_guard(0)

    assert created is True
    assert manager.created == [0]
    assert manager._startup_page_guard_active is False


def test_prewarm_waits_for_startup_then_runs_after_idle_delay(monkeypatch):
    manager = _Manager()
    timers = _install_timer(monkeypatch)
    manager._begin_startup_page_guard()

    assert manager.prewarmPage(1) is True
    assert manager.created == []
    assert timers.calls == []

    manager._complete_startup_page_guard(0)
    assert [delay for delay, _callback in timers.calls] == [250]
    timers.run_next()

    assert manager.created == [1]
    assert manager._pages[1]._prismqml_async_page is False


def test_prewarm_does_not_run_before_window_exists(monkeypatch):
    manager = _Manager()
    timers = _install_timer(monkeypatch)
    manager._window = None

    assert manager.prewarmPage(1) is True
    assert timers.calls == []

    manager._window = object()
    manager._schedule_page_prewarm()
    assert [delay for delay, _callback in timers.calls] == [250]


def test_prewarm_yields_while_foreground_page_is_loading(monkeypatch):
    manager = _Manager()
    timers = _install_timer(monkeypatch)
    manager._begin_startup_page_guard()
    manager._complete_startup_page_guard(0)
    manager._mark_foreground_page_load_started(2)

    assert manager.prewarmPage(1) is True
    assert manager.created == []
    assert timers.calls == []

    manager._mark_foreground_page_load_finished()
    timers.run_next()
    assert manager.created == [1]


def test_prewarm_queue_keeps_only_one_managed_page_in_flight(monkeypatch):
    manager = _Manager()
    timers = _install_timer(monkeypatch)
    manager._begin_startup_page_guard()
    manager._complete_startup_page_guard(0)

    def create_managed(index):
        manager.created.append(index)
        manager._pages[index] = SimpleNamespace(_prismqml_async_page=True)

    manager._create_page = create_managed
    assert manager.prewarmPage(1) is True
    assert manager.prewarmPage(2) is True

    timers.run_next()
    assert manager.created == [1]
    assert manager._page_prewarm_in_flight == 1
    assert timers.calls == []

    manager._finish_page_prewarm(1)
    assert [delay for delay, _callback in timers.calls] == [250]
    timers.run_next()
    assert manager.created == [1, 2]


def test_duplicate_or_current_prewarm_request_is_ignored(monkeypatch):
    manager = _Manager()
    timers = _install_timer(monkeypatch)
    manager._begin_startup_page_guard()

    assert manager.prewarmPage(0) is False
    assert manager.prewarmPage(1) is True
    assert manager.prewarmPage(1) is False
    assert timers.calls == []
