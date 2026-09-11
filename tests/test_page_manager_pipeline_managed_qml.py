# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""PageManager managed async QML page characterization. 托管异步 QML 页面现状合同。"""

from __future__ import annotations

from prismqml.python.window import _page_prewarm

from page_manager_shared import (
    _PAGE_RENDER_DELAY_MS,
    _AsyncPage,
    _Container,
    _install_runtime_fakes,
    _new_manager,
    _source_item,
)


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
