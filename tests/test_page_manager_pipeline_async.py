# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""PageManager async pipeline characterization. 异步页面加载管线现状合同。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
import shiboken6

from prismqml.python.window import _page_manager

from page_manager_shared import (
    _ASYNC_SIZE_DELAYS_MS,
    _PAGE_RENDER_DELAY_MS,
    _SYNC_SIZE_DELAY_MS,
    _Container,
    _Page,
    _PageItem,
    _Signal,
    _assert_async_ready_events,
    _empty_item,
    _exercise_async_size_retries,
    _install_runtime_fakes,
    _new_manager,
    _source_item,
)


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
