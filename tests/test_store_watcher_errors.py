# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Store watcher error isolation regressions. Store 观察者错误隔离回归。"""

import prismqml.python.state.store as store_module
from prismqml.python.state.store import Store


def _failing_watcher(message):
    def fail(*_args):
        raise RuntimeError(message)

    return fail


def test_failed_key_watcher_keeps_later_observers_and_signal(monkeypatch):
    store = Store("errors")
    events = []
    logged = []
    monkeypatch.setattr(store_module, "exception", logged.append)
    store.define("count", 0)
    store.watch("count", _failing_watcher("key watcher failed"))
    store.watch("count", lambda new, old: events.append(("key", new, old)))
    store.watch_all(lambda key, new, old: events.append(("global", key, new, old)))
    store.qt_signals.changed.connect(
        lambda key, new, old: events.append(("signal", key, new, old))
    )

    store.set("count", 1)

    assert events == [("key", 1, 0), ("global", "count", 1, 0), ("signal", "count", 1, 0)]
    assert logged == [
        "[Store:errors] Watcher error for 'count': RuntimeError: key watcher failed"
    ]


def test_failed_global_watcher_keeps_later_observer_and_signal(monkeypatch):
    store = Store("errors")
    events = []
    logged = []
    monkeypatch.setattr(store_module, "exception", logged.append)
    store.define("count", 0)
    store.watch_all(_failing_watcher("global watcher failed"))
    store.watch_all(lambda key, new, old: events.append(("global", key, new, old)))
    store.qt_signals.changed.connect(
        lambda key, new, old: events.append(("signal", key, new, old))
    )

    store.set("count", 1)

    assert events == [("global", "count", 1, 0), ("signal", "count", 1, 0)]
    assert logged == [
        "[Store:errors] Global watcher error for 'count': "
        "RuntimeError: global watcher failed"
    ]
