# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Latest-target navigation regressions. 最新目标导航回归。"""

from types import SimpleNamespace

from prismqml.python.window import _page_prewarm, window_core
from prismqml.python.window._page_manager import PageManagerMixin


class _Signal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self, *args):
        for callback in tuple(self.callbacks):
            callback(*args)


class _ManagedPage:
    _prismqml_async_page = True

    def __init__(self):
        self._qml_item = None
        self._deferred_queue = []
        self.page_ready = _Signal()
        self.page_failed = _Signal()
        self.start_count = 0

    def start_loading(self):
        self.start_count += 1


class _Manager(PageManagerMixin):
    def __init__(self, page_count=2, *, delay_factories=False):
        self._window = object()
        self._lazy_loading = True
        self._current_index = -1
        self._pages = {}
        self._bottom_nav_items = []
        self._nav_items = []
        self.currentIndexChanged = _Signal()
        self.events = []
        self.pending_factories = []
        self.delay_factories = delay_factories
        self.factory_counts = [0] * page_count
        self.pages = [_ManagedPage() for _index in range(page_count)]
        for index, page in enumerate(self.pages):
            self._nav_items.append(self._make_item(index, page))
        _page_prewarm.initialize_page_prewarm_state(self)

    def _make_item(self, index, page):
        def get_page():
            self.factory_counts[index] += 1
            return page

        return SimpleNamespace(
            text=f"Page {index}",
            page_getter=get_page,
            page_class=None,
            _page_instance=None,
        )

    def _find_child_by_name(self, name):
        return SimpleNamespace(name=name)

    def _schedule_async_page_creation(self, item, on_page_ready):
        if self.delay_factories:
            self.pending_factories.append((item, on_page_ready))
            return
        on_page_ready(item.page_getter())

    def _start_loading_overlay(self, index):
        self.events.append(("loading", index))

    def _mark_python_page_ready(self, index):
        self.events.append(("ready", index))

    def _finish_loading(self):
        self.events.append(("finish",))
        self._mark_foreground_page_load_finished()

    def _switch_to_index(self, index):
        self.events.append(("switch", index))


def _events(manager, name):
    return [event for event in manager.events if event[0] == name]


def test_old_target_ready_first_does_not_finish_or_steal_new_target():
    manager = _Manager()

    manager._on_nav_changed(0)
    manager._on_nav_changed(1)
    manager.pages[0].page_ready.emit()

    assert _events(manager, "ready") == [("ready", 0)]
    assert _events(manager, "finish") == []
    assert _events(manager, "switch") == []

    manager.pages[1].page_ready.emit()

    assert _events(manager, "finish") == [("finish",)]
    assert _events(manager, "switch") == [("switch", 1)]


def test_old_target_ready_last_cannot_steal_completed_new_target():
    manager = _Manager()

    manager._on_nav_changed(0)
    manager._on_nav_changed(1)
    manager.pages[1].page_ready.emit()
    manager.pages[0].page_ready.emit()

    assert _events(manager, "ready") == [("ready", 1), ("ready", 0)]
    assert _events(manager, "finish") == [("finish",)]
    assert _events(manager, "switch") == [("switch", 1)]


def test_old_target_failure_does_not_finish_new_target_loading():
    manager = _Manager()

    manager._on_nav_changed(0)
    manager._on_nav_changed(1)
    manager.pages[0].page_failed.emit("page zero failed")

    assert 0 not in manager._pages
    assert _events(manager, "finish") == []

    manager.pages[1].page_ready.emit()

    assert _events(manager, "finish") == [("finish",)]
    assert _events(manager, "switch") == [("switch", 1)]


def test_revisiting_page_in_flight_promotes_existing_load():
    manager = _Manager()

    manager._on_nav_changed(0)
    manager._on_nav_changed(1)
    manager._on_nav_changed(0)

    assert _events(manager, "loading") == [
        ("loading", 0),
        ("loading", 1),
        ("loading", 0),
    ]
    assert _events(manager, "switch") == []
    assert manager.factory_counts == [1, 1]

    manager.pages[0].page_ready.emit()

    assert _events(manager, "switch") == [("switch", 0)]


def test_revisiting_before_factory_runs_does_not_duplicate_creation():
    manager = _Manager(delay_factories=True)

    manager._on_nav_changed(0)
    manager._on_nav_changed(1)
    manager._on_nav_changed(0)

    assert len(manager.pending_factories) == 2
    assert _events(manager, "loading") == [
        ("loading", 0),
        ("loading", 1),
        ("loading", 0),
    ]

    for item, callback in tuple(manager.pending_factories):
        callback(item.page_getter())

    assert manager.factory_counts == [1, 1]


def test_ready_page_retarget_cancels_replaced_loading():
    manager = _Manager()
    manager._pages[0] = manager.pages[0]
    manager._current_index = 0

    manager._on_nav_changed(1)
    manager._on_nav_changed(0)

    assert _events(manager, "finish") == [("finish",)]
    assert _events(manager, "switch") == [("switch", 0)]

    manager.pages[1].page_ready.emit()

    assert _events(manager, "finish") == [("finish",)]
    assert _events(manager, "switch") == [("switch", 0)]


def test_programmatic_navigation_uses_shared_latest_target_path():
    calls = []
    owner = SimpleNamespace(
        _nav_items=[object(), object()],
        _bottom_nav_items=[],
        _request_page_navigation=lambda index, **kwargs: calls.append(
            (index, kwargs)
        ),
    )

    window_core.WindowCore.setCurrentIndex(owner, 1)

    assert calls == [(1, {"switch_immediately": True})]
