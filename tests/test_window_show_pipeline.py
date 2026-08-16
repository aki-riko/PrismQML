# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""WindowCore.show characterization. 窗口显示编排现状合同。"""

from __future__ import annotations

import re
from types import SimpleNamespace

import pytest

from prismqml.python import config
from prismqml.python.window import window_core


_PROFILE_PATTERN = re.compile(
    r"^\[启动剖析\] WindowCore\.show (?P<label>.+): \+\d+ms / total \d+ms$"
)
_ERROR_TYPES = (RuntimeError, ValueError, KeyboardInterrupt, SystemExit)


def _current_marker(manager, previous):
    current = window_core.WindowCore._current_window_instance
    if current is manager:
        return "manager"
    if current is previous:
        return "previous"
    return "other"


class _RecordingWindow:
    def __init__(self, calls, manager, previous, error=None):
        self._calls = calls
        self._manager = manager
        self._previous = previous
        self._error = error

    def show(self):
        self._calls.append(
            ("native_show", _current_marker(self._manager, self._previous))
        )
        if self._error is not None:
            raise self._error


@pytest.fixture
def manager(monkeypatch):
    config_manager = SimpleNamespace(
        lazyLoading=True,
        appearancePersistenceEnabled=True,
        _bind_appearance_runtime=lambda _callback, *, apply_persisted=True: None,
    )
    monkeypatch.setattr(config, "getConfigManager", lambda: config_manager)
    original_current = window_core.WindowCore._current_window_instance
    previous = object()
    window_core.WindowCore._current_window_instance = previous
    try:
        instance = window_core.WindowCore()
        yield instance, previous
    finally:
        window_core.WindowCore._current_window_instance = original_current


def _record_profile(calls):
    def record(message):
        match = _PROFILE_PATTERN.fullmatch(message)
        assert match is not None
        calls.append(("profile", match.group("label")))

    return record


def _new_show_events(marker):
    return [
        ("create", marker),
        ("profile", "_create_window"),
        ("prepare", marker),
        ("profile", "show 前准备首帧"),
        ("native_show", marker),
        ("profile", "QQuickWindow.show"),
    ]


def _reused_show_events(marker):
    return [
        ("profile", "复用已有窗口"),
        ("restore", marker),
        ("profile", "show 前恢复可见状态"),
        ("native_show", marker),
        ("profile", "QQuickWindow.show"),
        ("restore", marker),
        ("profile", "show 后恢复可见状态"),
    ]


class _ShowScenario:
    def __init__(
        self,
        manager,
        previous,
        calls,
        *,
        create_error=None,
        create_error_after_install=False,
        native_error=None,
        restore_error=None,
        restore_error_call=1,
        page_error=None,
        page_error_index=0,
        create_result=True,
    ):
        self._manager = manager
        self._previous = previous
        self._calls = calls
        self._create_error = create_error
        self._create_error_after_install = create_error_after_install
        self._restore_error = restore_error
        self._restore_error_call = restore_error_call
        self._page_error = page_error
        self._page_error_index = page_error_index
        self._create_result = create_result
        self._restore_calls = 0
        self.window = _RecordingWindow(
            calls, manager, previous, error=native_error
        )

    def create_window(self):
        self._calls.append(
            ("create", _current_marker(self._manager, self._previous))
        )
        if self._create_error is not None and not self._create_error_after_install:
            raise self._create_error
        if self._create_result:
            self._manager._window = self.window
        if self._create_error is not None:
            raise self._create_error

    def restore_visible_state(self):
        self._restore_calls += 1
        self._calls.append(
            ("restore", _current_marker(self._manager, self._previous))
        )
        if (
            self._restore_error is not None
            and self._restore_calls == self._restore_error_call
        ):
            raise self._restore_error

    def prepare_initial_frame(self):
        self._calls.append(
            ("prepare", _current_marker(self._manager, self._previous))
        )

    def ensure_page(self, index):
        self._calls.append(
            ("page", index, _current_marker(self._manager, self._previous))
        )
        if self._page_error is not None and index == self._page_error_index:
            raise self._page_error
        self._manager._pages.setdefault(index, object())

    def install(self, monkeypatch):
        monkeypatch.setattr(self._manager, "_create_window", self.create_window)
        monkeypatch.setattr(
            self._manager, "_restore_visible_state", self.restore_visible_state
        )
        monkeypatch.setattr(
            self._manager,
            "_prepare_initial_frame",
            self.prepare_initial_frame,
            raising=False,
        )
        monkeypatch.setattr(
            self._manager, "_ensure_page_created", self.ensure_page
        )
        monkeypatch.setattr(window_core, "debug", _record_profile(self._calls))
        return self.window


def test_show_creates_window_without_restore_and_publishes_before_lazy_home(
    manager, monkeypatch
):
    instance, previous = manager
    calls = []
    instance._nav_items = [object()]
    _ShowScenario(instance, previous, calls).install(monkeypatch)

    instance.show()

    assert calls == _new_show_events("previous") + [
        ("page", 0, "manager"),
        ("profile", "创建/确认首页"),
    ]
    assert window_core.WindowCore._current_window_instance is instance


def test_show_stops_after_create_when_no_window_was_produced(manager, monkeypatch):
    instance, previous = manager
    calls = []
    instance._nav_items = [object()]
    scenario = _ShowScenario(instance, previous, calls, create_result=False)
    scenario.install(monkeypatch)

    instance.show()

    assert calls == _new_show_events("previous")[:2]
    assert instance._window is None
    assert window_core.WindowCore._current_window_instance is previous


def test_show_reused_window_restores_before_and_after_native_show(
    manager, monkeypatch
):
    instance, previous = manager
    calls = []
    instance._nav_items = [object()]
    instance._window = _ShowScenario(instance, previous, calls).install(
        monkeypatch
    )

    instance.show()

    assert calls == _reused_show_events("previous") + [
        ("page", 0, "manager"),
        ("profile", "创建/确认首页"),
    ]
    assert window_core.WindowCore._current_window_instance is instance


def test_repeated_show_reuses_root_but_repeats_show_restore_and_home(
    manager, monkeypatch
):
    instance, previous = manager
    calls = []
    instance._nav_items = [object()]
    _ShowScenario(instance, previous, calls).install(monkeypatch)

    instance.show()
    first_run_length = len(calls)
    instance.show()

    assert [event[0] for event in calls].count("create") == 1
    assert [event[0] for event in calls].count("native_show") == 2
    assert [event[0] for event in calls].count("restore") == 2
    assert [event[:2] for event in calls].count(("page", 0)) == 2
    assert calls[first_run_length:] == _reused_show_events("manager") + [
        ("page", 0, "manager"),
        ("profile", "创建/确认首页"),
    ]


def test_lazy_show_without_navigation_does_not_create_page(manager, monkeypatch):
    instance, previous = manager
    calls = []
    instance._window = _ShowScenario(instance, previous, calls).install(
        monkeypatch
    )

    instance.show()

    assert calls == _reused_show_events("previous")
    assert window_core.WindowCore._current_window_instance is instance


def test_borrowed_show_skips_unavailable_startup_guard_hooks(monkeypatch):
    calls = []
    previous = window_core.WindowCore._current_window_instance
    owner = SimpleNamespace(
        _window=SimpleNamespace(show=lambda: calls.append("show")),
        _lazy_loading=True,
        _nav_items=[],
        _bottom_nav_items=[],
        _restore_visible_state=lambda: calls.append("restore"),
    )
    monkeypatch.setattr(window_core, "debug", lambda _message: None)

    try:
        window_core.WindowCore.show(owner)
    finally:
        window_core.WindowCore._current_window_instance = previous

    assert calls == ["restore", "show", "restore"]


def test_lazy_show_with_only_bottom_navigation_creates_local_home(
    manager, monkeypatch
):
    instance, previous = manager
    calls = []
    instance._bottom_nav_items = [object()]
    instance._window = _ShowScenario(instance, previous, calls).install(monkeypatch)

    instance.show()

    assert calls == _reused_show_events("previous") + [
        ("page", 0, "manager"),
        ("profile", "创建/确认首页"),
    ]


def test_eager_show_creates_top_and_bottom_pages_in_combined_order(
    manager, monkeypatch
):
    instance, previous = manager
    calls = []
    instance._lazy_loading = False
    instance._nav_items = [object(), object()]
    instance._bottom_nav_items = [object()]
    instance._window = _ShowScenario(instance, previous, calls).install(monkeypatch)

    instance.show()

    assert calls == _reused_show_events("previous") + [
        ("page", 0, "manager"),
        ("page", 1, "manager"),
        ("page", 2, "manager"),
        ("profile", "创建/确认全部页面"),
    ]


def test_eager_show_without_navigation_still_profiles_empty_batch(
    manager, monkeypatch
):
    instance, previous = manager
    calls = []
    instance._lazy_loading = False
    instance._window = _ShowScenario(instance, previous, calls).install(monkeypatch)

    instance.show()

    assert calls == _reused_show_events("previous") + [
        ("profile", "创建/确认全部页面")
    ]
    assert window_core.WindowCore._current_window_instance is instance


def _assert_raises_same(error_type, expected_error, action):
    with pytest.raises(error_type) as exc_info:
        action()
    assert exc_info.value is expected_error


@pytest.mark.parametrize("error_type", _ERROR_TYPES)
def test_create_failures_propagate_before_profile_or_current_publish(
    manager, monkeypatch, error_type
):
    instance, previous = manager
    calls = []
    expected_error = error_type("create failed")
    scenario = _ShowScenario(
        instance, previous, calls, create_error=expected_error
    )
    scenario.install(monkeypatch)

    _assert_raises_same(error_type, expected_error, instance.show)

    assert calls == _new_show_events("previous")[:1]
    assert instance._window is None
    assert window_core.WindowCore._current_window_instance is previous


@pytest.mark.parametrize("error_type", _ERROR_TYPES)
def test_create_failures_after_root_install_keep_partial_root_unpublished(
    manager, monkeypatch, error_type
):
    instance, previous = manager
    calls = []
    expected_error = error_type("create failed after root install")
    scenario = _ShowScenario(
        instance,
        previous,
        calls,
        create_error=expected_error,
        create_error_after_install=True,
    )
    scenario.install(monkeypatch)

    _assert_raises_same(error_type, expected_error, instance.show)

    assert calls == _new_show_events("previous")[:1]
    assert instance._window is scenario.window
    assert window_core.WindowCore._current_window_instance is previous


@pytest.mark.parametrize("error_type", _ERROR_TYPES)
def test_native_show_failures_stop_after_reuse_pre_restore(
    manager, monkeypatch, error_type
):
    instance, previous = manager
    calls = []
    expected_error = error_type("native show failed")
    scenario = _ShowScenario(
        instance, previous, calls, native_error=expected_error
    )
    instance._window = scenario.install(monkeypatch)

    _assert_raises_same(error_type, expected_error, instance.show)

    assert calls == _reused_show_events("previous")[:4]
    assert window_core.WindowCore._current_window_instance is previous


@pytest.mark.parametrize("error_type", _ERROR_TYPES)
def test_native_show_failures_after_create_keep_partial_root_unpublished(
    manager, monkeypatch, error_type
):
    instance, previous = manager
    calls = []
    expected_error = error_type("new native show failed")
    scenario = _ShowScenario(
        instance, previous, calls, native_error=expected_error
    )
    scenario.install(monkeypatch)

    _assert_raises_same(error_type, expected_error, instance.show)

    assert calls == _new_show_events("previous")[:5]
    assert instance._window is scenario.window
    assert window_core.WindowCore._current_window_instance is previous


@pytest.mark.parametrize("error_type", _ERROR_TYPES)
def test_pre_show_restore_failures_propagate_before_native_show(
    manager, monkeypatch, error_type
):
    instance, previous = manager
    calls = []
    expected_error = error_type("pre-show restore failed")
    scenario = _ShowScenario(
        instance, previous, calls, restore_error=expected_error
    )
    instance._window = scenario.install(monkeypatch)

    _assert_raises_same(error_type, expected_error, instance.show)

    assert calls == _reused_show_events("previous")[:2]
    assert window_core.WindowCore._current_window_instance is previous


@pytest.mark.parametrize("error_type", _ERROR_TYPES)
def test_post_show_restore_failures_keep_current_unpublished(
    manager, monkeypatch, error_type
):
    instance, previous = manager
    calls = []
    expected_error = error_type("post-show restore failed")
    scenario = _ShowScenario(
        instance,
        previous,
        calls,
        restore_error=expected_error,
        restore_error_call=2,
    )
    instance._window = scenario.install(monkeypatch)

    _assert_raises_same(error_type, expected_error, instance.show)

    assert calls == _reused_show_events("previous")[:-1]
    assert window_core.WindowCore._current_window_instance is previous


@pytest.mark.parametrize("error_type", _ERROR_TYPES)
def test_lazy_home_failures_keep_published_window_and_stop_profile(
    manager, monkeypatch, error_type
):
    instance, previous = manager
    calls = []
    instance._nav_items = [object()]
    expected_error = error_type("lazy home failed")
    scenario = _ShowScenario(
        instance, previous, calls, page_error=expected_error
    )
    scenario.install(monkeypatch)

    _assert_raises_same(error_type, expected_error, instance.show)

    assert calls == _new_show_events("previous") + [
        ("page", 0, "manager"),
    ]
    assert instance._window is scenario.window
    assert window_core.WindowCore._current_window_instance is instance


@pytest.mark.parametrize("error_type", _ERROR_TYPES)
def test_eager_page_failures_keep_published_window_and_stop_later_indexes(
    manager, monkeypatch, error_type
):
    instance, previous = manager
    calls = []
    instance._lazy_loading = False
    instance._nav_items = [object(), object()]
    instance._bottom_nav_items = [object()]
    expected_error = error_type("eager page failed")
    scenario = _ShowScenario(
        instance,
        previous,
        calls,
        page_error=expected_error,
        page_error_index=1,
    )
    instance._window = scenario.install(monkeypatch)

    _assert_raises_same(error_type, expected_error, instance.show)

    assert calls == _reused_show_events("previous") + [
        ("page", 0, "manager"),
        ("page", 1, "manager"),
    ]
    assert list(instance._pages) == [0]
    assert window_core.WindowCore._current_window_instance is instance
