# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""PageManager pipeline characterization. 页面管理管线现状合同。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from prismqml.python.window import _page_prewarm

from page_manager_shared import (
    _SYNC_SIZE_DELAY_MS,
    _Container,
    _Page,
    _assert_sync_size_result,
    _install_runtime_fakes,
    _new_manager,
    _source_item,
)


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
        expected.append(("batch", True))
    else:
        expected.append(("invoke", "_markPythonPageReady", 1))
    assert events == expected
    assert manager._pages[1] is page and item._page_instance is page
    if deferred:
        assert page.batch_callback is not None
        assert not any(
            event[:2] == ("invoke", "_markPythonPageReady")
            for event in events
        )
        page.batch_callback()
        assert events[-1] == ("invoke", "_markPythonPageReady", 1)
    _assert_sync_size_result(timers, container, events, size)
    assert not any(
        event[0] == "emit" and event[1] in {"page_width", "page_height"}
        for event in events
    )


def test_sync_deferred_startup_page_keeps_guard_until_batch_complete(monkeypatch):
    events = []
    page = _Page(events, deferred=True)
    item = _source_item("existing", page, events)
    manager = _new_manager(events, item, _Container(events))
    _page_prewarm.initialize_page_prewarm_state(manager)
    manager._current_index = 0
    manager._begin_startup_page_guard()
    _install_runtime_fakes(monkeypatch, events)

    manager._create_page(0)

    assert page.batch_callback is not None
    assert manager._startup_page_guard_active is True
    assert not any(
        event[:2] == ("invoke", "_markPythonPageReady")
        for event in events
    )

    page.batch_callback()

    assert events[-1] == ("invoke", "_markPythonPageReady", 0)
    assert manager._startup_page_guard_active is False


def test_sync_deferred_prewarm_promotes_only_after_batch_complete(monkeypatch):
    events = []
    page = _Page(events, deferred=True)
    item = _source_item("existing", page, events)
    manager = _new_manager(events, item, _Container(events))
    _page_prewarm.initialize_page_prewarm_state(manager)
    manager._current_index = 0
    manager._page_prewarm_in_flight = 0
    manager._foreground_page_load_index = 0
    _install_runtime_fakes(monkeypatch, events)

    manager._create_page(0)

    assert page.batch_callback is not None
    assert not any(event[0] in {"finish", "switch"} for event in events)

    page.batch_callback()

    assert manager._page_prewarm_in_flight is None
    assert events[-3:] == [
        ("invoke", "_markPythonPageReady", 0),
        ("finish",),
        ("switch", 0),
    ]


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
