# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""PageManager pipeline characterization. 页面管理管线现状合同。"""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest
import shiboken6

from prismqml.python.window import _page_manager, _page_prewarm


_PAGE_RENDER_DELAY_MS = 16
_SYNC_SIZE_DELAY_MS = 50
_ASYNC_SIZE_DELAYS_MS = (50, 200)


class _Signal:
    def __init__(self, name, events):
        self.name = name
        self.events = events
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)
        self.events.append(("connect", self.name))

    def emit(self, *args):
        self.events.append(("emit", self.name, *args))

    def fire(self, *args):
        self.events.append(("fire", self.name, *args))
        for callback in tuple(self.callbacks):
            callback(*args)


class _TimerQueue:
    def __init__(self, events):
        self.events = events
        self.calls = []

    @property
    def delays(self):
        return [delay for delay, _callback in self.calls]

    def single_shot(self, delay, callback):
        self.events.append(("timer", delay))
        self.calls.append((delay, callback))

    def run(self, delay):
        for index, (actual_delay, callback) in enumerate(self.calls):
            if actual_delay == delay:
                self.calls.pop(index)
                callback()
                return
        raise AssertionError(f"timer {delay} not scheduled")


class _PageItem:
    def __init__(self, events):
        self.events = events
        self.widthChanged = _Signal("page_width", events)
        self.heightChanged = _Signal("page_height", events)

    def setParentItem(self, container):
        self.events.append(("parent", container.name))

    def setWidth(self, width):
        self.events.append(("set_width", width))

    def setHeight(self, height):
        self.events.append(("set_height", height))

    def setOpacity(self, opacity):
        self.events.append(("opacity", opacity))


class _Container:
    def __init__(self, events, name="page_0", width=640, height=480):
        self.events = events
        self.name = name
        self.current_width = width
        self.current_height = height
        self.widthChanged = _Signal("container_width", events)
        self.heightChanged = _Signal("container_height", events)

    def width(self):
        return self.current_width

    def height(self):
        return self.current_height


class _Page:
    def __init__(self, events, *, deferred=False, batch_error=None):
        self.events = events
        self._qml_item = _PageItem(events)
        self._deferred_value = [object()] if deferred else []
        self.track_deferred_reads = False
        self.deferred_reads = 0
        self.batch_error = batch_error
        self.batch_callback = None

    @property
    def _deferred_queue(self):
        self.deferred_reads += 1
        if self.track_deferred_reads:
            self.events.append(("deferred_read", self.deferred_reads))
        return self._deferred_value

    def startBatchCreation(self, on_complete=None):
        self.events.append(("batch", on_complete is not None))
        if self.batch_error is not None:
            raise self.batch_error("batch failed")
        self.batch_callback = on_complete


def test_size_binder_uses_stable_async_layout_item(monkeypatch):
    qml_events = []
    layout_events = []
    container_events = []
    page = _Page(qml_events)
    page._prismqml_layout_item = _PageItem(layout_events)
    container = _Container(container_events, width=900, height=640)
    monkeypatch.setattr(shiboken6, "isValid", lambda _item: True)

    bind_size = _page_manager._make_page_size_binder(page, container, False)
    bind_size()

    assert qml_events == []
    assert layout_events == [("set_width", 900), ("set_height", 640)]


class _AsyncPage(_Page):
    _prismqml_async_page = True

    def __init__(self, events, *, start_error=None):
        super().__init__(events)
        self.page_ready = _Signal("async_page_ready", events)
        self.page_failed = _Signal("async_page_failed", events)
        self.start_error = start_error

    def start_loading(self):
        self.events.append(("start_async_qml",))
        if self.start_error is not None:
            raise self.start_error("start failed")


class _RecordingPages(dict):
    def __init__(self, events):
        super().__init__()
        self.events = events

    def __setitem__(self, index, page):
        self.events.append(("register", index))
        super().__setitem__(index, page)


class _Manager(_page_manager.PageManagerMixin):
    def __init__(self, events, top_items, bottom_items, container):
        self.events = events
        self._window = object()
        self._nav_items = list(top_items)
        self._bottom_nav_items = list(bottom_items)
        self._pages = _RecordingPages(events)
        self._lazy_loading = True
        self._current_index = -1
        self.currentIndexChanged = _Signal("current_index", events)
        self.container = container

    def _find_child_by_name(self, name):
        self.events.append(("find", name))
        return self.container

    def _finish_loading(self):
        self.events.append(("finish",))

    def _switch_to_index(self, index):
        self.events.append(("switch", index))


def _install_runtime_fakes(monkeypatch, events):
    timers = _TimerQueue(events)

    def invoke_method(_window, method, *args):
        value = args[0][1] if args else None
        events.append(("invoke", method, value))
        return True

    def record_exception(message):
        events.append(("exception", message, sys.exc_info()[0]))

    monkeypatch.setattr(
        _page_manager, "QMetaObject", SimpleNamespace(invokeMethod=invoke_method)
    )
    monkeypatch.setattr(_page_manager, "Q_ARG", lambda name, value: (name, value))
    monkeypatch.setattr(
        _page_manager, "QTimer", SimpleNamespace(singleShot=timers.single_shot)
    )
    monkeypatch.setattr(
        _page_prewarm, "QTimer", SimpleNamespace(singleShot=timers.single_shot)
    )
    monkeypatch.setattr(_page_manager, "debug", lambda *_args: None)
    monkeypatch.setattr(
        _page_manager,
        "warning",
        lambda message: events.append(("warning", message)),
    )
    monkeypatch.setattr(_page_manager, "exception", record_exception)
    monkeypatch.setattr(shiboken6, "isValid", lambda _item: True)
    return timers


def _empty_item(text="Empty"):
    return SimpleNamespace(
        text=text, page_getter=None, page_class=None, _page_instance=None
    )


def _source_item(source, page, events):
    fallback_page = object()

    def getter():
        events.append(("getter",))
        return page if source == "getter" else fallback_page

    def page_class():
        events.append(("class",))
        return page if source == "class" else fallback_page

    return SimpleNamespace(
        text="Target",
        page_getter=getter if source in {"existing", "getter"} else None,
        page_class=page_class,
        _page_instance=page if source == "existing" else None,
    )


def _new_manager(events, item, container, *, bottom=False):
    top_items = [_empty_item()] if bottom else [item]
    bottom_items = [item] if bottom else []
    return _Manager(events, top_items, bottom_items, container)


def _assert_async_ready_events(events):
    assert events[4:] == [
        ("getter",), ("parent", "page_1"),
        ("connect", "container_width"), ("connect", "container_height"),
        ("timer", _ASYNC_SIZE_DELAYS_MS[0]),
        ("timer", _ASYNC_SIZE_DELAYS_MS[1]),
        ("register", 1),
        ("invoke", "_markPythonPageReady", 1),
        ("finish",), ("switch", 1),
    ]


def _exercise_async_size_retries(timers, container, events):
    size_callback = timers.calls[0][1]
    assert timers.calls[1][1] is size_callback
    assert container.widthChanged.callbacks == [size_callback]
    assert container.heightChanged.callbacks == [size_callback]
    for width, height in ((0, 480), (640, 0)):
        container.current_width = width
        container.current_height = height
        before_zero_size = list(events)
        container.widthChanged.callbacks[0]()
        assert events == before_zero_size
    container.current_width, container.current_height = 640, 480
    timers.run(_ASYNC_SIZE_DELAYS_MS[0])
    assert events[-4:] == [
        ("set_width", 640), ("set_height", 480),
        ("emit", "page_width"), ("emit", "page_height"),
    ]
    before_retry = len(events)
    timers.run(_ASYNC_SIZE_DELAYS_MS[1])
    assert events[before_retry:] == events[before_retry - 4:before_retry]


def _assert_sync_size_result(timers, container, events, size):
    size_callback = timers.calls[0][1]
    assert container.widthChanged.callbacks == [size_callback]
    assert container.heightChanged.callbacks == [size_callback]
    before_size = list(events)
    timers.run(_SYNC_SIZE_DELAY_MS)
    if all(dimension > 0 for dimension in size):
        assert events[-2:] == [("set_width", 640), ("set_height", 480)]
    else:
        assert events == before_size


@pytest.mark.parametrize(
    ("source", "deferred", "size"),
    [
        ("existing", True, (640, 480)),
        ("getter", False, (0, 480)),
        ("class", True, (640, 0)),
    ],
)
def test_sync_page_pipeline_preserves_source_priority_and_global_index(
    monkeypatch, source, deferred, size
):
    events = []
    page = _Page(events, deferred=deferred)
    page.track_deferred_reads = True
    item = _source_item(source, page, events)
    container = _Container(events, "page_1", width=size[0], height=size[1])
    manager = _new_manager(events, item, container, bottom=True)
    timers = _install_runtime_fakes(monkeypatch, events)

    manager._create_page(1)

    source_events = [] if source == "existing" else [(source,)]
    expected = [
        ("find", "page_1"), *source_events, ("parent", "page_1"),
        ("connect", "container_width"), ("connect", "container_height"),
        ("timer", _SYNC_SIZE_DELAY_MS), ("register", 1),
        ("deferred_read", 1), ("deferred_read", 2),
    ]
    if deferred:
        expected.append(("batch", False))
    expected.append(("invoke", "_markPythonPageReady", 1))
    assert events == expected
    assert manager._pages[1] is page and item._page_instance is page
    _assert_sync_size_result(timers, container, events, size)
    assert not any(
        event[0] == "emit" and event[1] in {"page_width", "page_height"}
        for event in events
    )


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_size_binding_reads_current_qml_item(monkeypatch, mode):
    events = []
    page = _Page(events)
    item = _source_item("existing" if mode == "sync" else "getter", page, events)
    manager = _new_manager(events, item, _Container(events))
    timers = _install_runtime_fakes(monkeypatch, events)

    if mode == "sync":
        manager._create_page(0)
    else:
        manager._start_async_page_load(0)
        timers.run(_PAGE_RENDER_DELAY_MS)

    replacement = _PageItem(events)
    replacement.widthChanged = _Signal("replacement_page_width", events)
    replacement.heightChanged = _Signal("replacement_page_height", events)
    replacement.setWidth = lambda width: events.append(("replacement_width", width))
    replacement.setHeight = lambda height: events.append(("replacement_height", height))
    page._qml_item = replacement
    timers.run(_SYNC_SIZE_DELAY_MS)
    expected_tail = [
        ("replacement_width", 640),
        ("replacement_height", 480),
    ] if mode == "sync" else [
        ("emit", "replacement_page_width"),
        ("emit", "replacement_page_height"),
    ]
    assert events[-2:] == expected_tail
    assert ("replacement_width", 640) in events
    assert ("replacement_height", 480) in events


def test_sync_missing_qml_item_warning_keeps_page_index(monkeypatch):
    events = []
    page = _Page(events)
    page._qml_item = None
    item = _source_item("existing", page, events)
    manager = _new_manager(events, item, _Container(events), bottom=True)
    timers = _install_runtime_fakes(monkeypatch, events)

    manager._create_page(1)

    assert ("warning", "[_create_page] page_1 _qml_item 为 None!") in events
    assert timers.delays == []
    assert manager._pages[1] is page


def test_async_page_source_priority_is_getter_then_class_then_existing():
    events = []
    getter_page, class_page, existing_page = object(), object(), object()
    item = SimpleNamespace(
        page_getter=lambda: events.append(("getter",)) or getter_page,
        page_class=lambda: events.append(("class",)) or class_page,
        _page_instance=existing_page,
    )
    assert _page_manager._resolve_async_page_instance(item) is getter_page
    item.page_getter = None
    assert _page_manager._resolve_async_page_instance(item) is class_page
    item.page_class = None
    assert _page_manager._resolve_async_page_instance(item) is existing_page
    assert events == [("getter",), ("class",)]


def test_async_page_pipeline_waits_one_frame_and_finishes_before_switch(
    monkeypatch,
):
    events = []
    page = _Page(events)
    item = _source_item("getter", page, events)
    container = _Container(events, "page_1")
    manager = _new_manager(events, item, container, bottom=True)
    timers = _install_runtime_fakes(monkeypatch, events)

    manager._on_nav_changed(1)

    assert events == [
        ("invoke", "_startPythonLoading", 1), ("find", "page_1"),
        ("timer", _PAGE_RENDER_DELAY_MS), ("emit", "current_index", 1),
    ]
    assert manager._pages == {}
    timers.run(_PAGE_RENDER_DELAY_MS)
    assert timers.delays == list(_ASYNC_SIZE_DELAYS_MS)
    _assert_async_ready_events(events)
    assert manager._pages[1] is page and item._page_instance is page
    _exercise_async_size_retries(timers, container, events)


def test_async_deferred_page_waits_for_batch_before_switch(monkeypatch):
    events = []
    page = _Page(events, deferred=True)
    page.track_deferred_reads = True
    item = _source_item("getter", page, events)
    manager = _new_manager(events, item, _Container(events))
    timers = _install_runtime_fakes(monkeypatch, events)

    manager._start_async_page_load(0)
    timers.run(_PAGE_RENDER_DELAY_MS)

    assert events[-7:] == [
        ("deferred_read", 1), ("deferred_read", 2), ("opacity", 0),
        ("register", 0), ("deferred_read", 3), ("deferred_read", 4),
        ("batch", True),
    ]
    assert page.batch_callback is not None
    assert manager._pages[0] is page and item._page_instance is page
    assert not any(event[0] in {"finish", "switch"} for event in events)
    page.batch_callback()
    assert events[-4:] == [
        ("opacity", 1),
        ("invoke", "_markPythonPageReady", 0),
        ("finish",),
        ("switch", 0),
    ]


def test_managed_async_qml_page_keeps_overlay_until_target_is_ready(monkeypatch):
    events = []
    page = _AsyncPage(events)
    item = _source_item("getter", page, events)
    manager = _new_manager(events, item, _Container(events))
    timers = _install_runtime_fakes(monkeypatch, events)

    manager._start_async_page_load(0)
    timers.run(_PAGE_RENDER_DELAY_MS)

    assert events[-4:] == [
        ("register", 0),
        ("connect", "async_page_ready"),
        ("connect", "async_page_failed"),
        ("start_async_qml",),
    ]
    assert not any(event[0] in {"finish", "switch"} for event in events)

    page.page_ready.fire()

    assert events[-4:] == [
        ("fire", "async_page_ready"),
        ("invoke", "_markPythonPageReady", 0),
        ("finish",),
        ("switch", 0),
    ]


def test_managed_async_qml_page_failure_clears_cached_instance(monkeypatch):
    events = []
    page = _AsyncPage(events)
    item = _source_item("getter", page, events)
    manager = _new_manager(events, item, _Container(events))
    timers = _install_runtime_fakes(monkeypatch, events)

    manager._start_async_page_load(0)
    timers.run(_PAGE_RENDER_DELAY_MS)
    page.page_failed.fire("broken target")

    assert manager._pages == {}
    assert item._page_instance is None
    assert events[-2:] == [("warning", "异步 QML 页面加载失败: broken target"), ("finish",)]
    assert not any(event[0] == "switch" for event in events)


def test_managed_async_qml_page_start_failure_keeps_traceback_and_cleans_up(monkeypatch):
    events = []
    page = _AsyncPage(events, start_error=RuntimeError)
    item = _source_item("getter", page, events)
    manager = _new_manager(events, item, _Container(events))
    timers = _install_runtime_fakes(monkeypatch, events)

    manager._start_async_page_load(0)
    timers.run(_PAGE_RENDER_DELAY_MS)

    exception_events = [event for event in events if event[0] == "exception"]
    assert len(exception_events) == 1
    assert "异步 QML 页面启动失败" in exception_events[0][1]
    assert exception_events[0][2] is RuntimeError
    assert manager._pages == {}
    assert item._page_instance is None
    assert events[-1] == ("finish",)


def test_sync_managed_async_qml_page_starts_after_registration(monkeypatch):
    events = []
    page = _AsyncPage(events)
    item = _source_item("existing", page, events)
    manager = _new_manager(events, item, _Container(events))
    _install_runtime_fakes(monkeypatch, events)

    manager._create_page(0)

    assert ("register", 0) in events
    assert events[-1] == ("start_async_qml",)
    assert not any(event[0] in {"finish", "switch"} for event in events)

    page.page_ready.fire()

    assert events[-2:] == [("fire", "async_page_ready"), ("invoke", "_markPythonPageReady", 0)]
    assert not any(event[0] in {"finish", "switch"} for event in events)


def test_sync_managed_async_qml_page_failure_clears_cached_instance(monkeypatch):
    events = []
    page = _AsyncPage(events)
    item = _source_item("existing", page, events)
    manager = _new_manager(events, item, _Container(events))
    _install_runtime_fakes(monkeypatch, events)

    manager._create_page(0)
    page.page_failed.fire("broken initial target")

    assert manager._pages == {}
    assert item._page_instance is None
    assert events[-2][0] == "warning"
    assert "异步 QML 页面加载失败: broken initial target" in events[-2][1]
    assert events[-1] == ("finish",)
    assert not any(event[0] == "switch" for event in events)


def test_managed_async_qml_page_prewarm_success_stays_background(monkeypatch):
    events = []
    page = _AsyncPage(events)
    item = _source_item("existing", page, events)
    manager = _new_manager(events, item, _Container(events))
    _page_prewarm.initialize_page_prewarm_state(manager)
    manager._page_prewarm_in_flight = 0
    timers = _install_runtime_fakes(monkeypatch, events)

    manager._create_page(0)
    page.page_ready.fire()

    assert manager._pages[0] is page
    assert manager._page_prewarm_in_flight is None
    assert events[-2:] == [
        ("fire", "async_page_ready"),
        ("invoke", "_markPythonPageReady", 0),
    ]
    assert 250 not in timers.delays
    assert not any(event[0] in {"finish", "switch"} for event in events)


def test_managed_async_qml_page_prewarm_failure_clears_background_page(monkeypatch):
    events = []
    page = _AsyncPage(events)
    item = _source_item("existing", page, events)
    manager = _new_manager(events, item, _Container(events))
    _page_prewarm.initialize_page_prewarm_state(manager)
    manager._page_prewarm_in_flight = 0
    timers = _install_runtime_fakes(monkeypatch, events)

    manager._create_page(0)
    page.page_failed.fire("broken prewarm target")

    assert manager._pages == {}
    assert item._page_instance is None
    assert manager._page_prewarm_in_flight is None
    assert events[-1][0] == "warning"
    assert "prewarm target" in events[-1][1]
    assert not any(event[0] in {"finish", "switch"} for event in events)
    assert 250 not in timers.delays


@pytest.mark.parametrize("case", ["invalid_index", "missing_container", "no_loader"])
def test_async_invalid_target_starts_then_finishes_without_timer(monkeypatch, case):
    events = []
    page = _Page(events)
    item = _source_item("getter", page, events)
    index = 1 if case == "invalid_index" else 0
    if case == "no_loader":
        item = _empty_item()
    container = None if case == "missing_container" else _Container(events)
    manager = _new_manager(events, item, container)
    timers = _install_runtime_fakes(monkeypatch, events)

    manager._start_async_page_load(index)

    expected = [("invoke", "_startPythonLoading", index)]
    if case != "invalid_index":
        expected.append(("find", "page_0"))
    expected.append(("finish",))
    assert events == expected
    assert timers.delays == [] and manager._pages == {}
    assert not any(event[0] == "switch" for event in events)


@pytest.mark.parametrize("source", ["getter", "class"])
@pytest.mark.parametrize(
    "error_type", [ValueError, RuntimeError, KeyboardInterrupt, SystemExit]
)
def test_sync_page_factory_exceptions_propagate(
    monkeypatch, source, error_type
):
    events = []

    def stop_create():
        raise error_type("stop")

    item = SimpleNamespace(
        text="Target",
        page_getter=stop_create if source == "getter" else None,
        page_class=stop_create if source == "class" else None,
        _page_instance=None,
    )
    manager = _new_manager(events, item, _Container(events))
    _install_runtime_fakes(monkeypatch, events)
    with pytest.raises(error_type, match="stop"):
        manager._create_page(0)
    assert manager._pages == {}
    assert not any(event[0] == "exception" for event in events)


@pytest.mark.parametrize(
    ("error_type", "propagates"),
    [
        (ValueError, False),
        (RuntimeError, False),
        (KeyboardInterrupt, True),
        (SystemExit, True),
    ],
)
def test_async_batch_failure_current_partial_state(
    monkeypatch, error_type, propagates
):
    events = []
    page = _Page(events, deferred=True, batch_error=error_type)
    item = _source_item("getter", page, events)
    manager = _new_manager(events, item, _Container(events))
    timers = _install_runtime_fakes(monkeypatch, events)

    manager._start_async_page_load(0)
    if propagates:
        with pytest.raises(error_type, match="batch failed"):
            timers.run(_PAGE_RENDER_DELAY_MS)
    else:
        timers.run(_PAGE_RENDER_DELAY_MS)

    assert item._page_instance is page and manager._pages[0] is page
    assert [event for event in events if event[0] == "opacity"] == [("opacity", 0)]
    assert ("switch", 0) not in events
    assert events.count(("finish",)) == int(not propagates)
    exception_events = [event for event in events if event[0] == "exception"]
    if propagates:
        assert exception_events == []
    else:
        assert len(exception_events) == 1
        assert "页面创建失败" in exception_events[0][1]
        assert exception_events[0][2] is error_type
