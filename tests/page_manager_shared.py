# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""PageManager pipeline shared fakes. 页面管理管线共享测试替身与断言设施。"""

import sys
from types import SimpleNamespace

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
