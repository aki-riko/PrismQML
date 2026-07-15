# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Store.set batching contracts. Store.set 批处理合同。"""

import inspect
from typing import get_type_hints

from prismqml import Store


def _attach_observers(store, *keys):
    events = []

    def record(label, key, new, old):
        events.append((label, key, new, old, store.values()))

    for key in keys:
        store.watch(
            key,
            lambda new, old, watched=key: record("key", watched, new, old),
        )
    store.watch_all(lambda key, new, old: record("global", key, new, old))
    store.qt_signals.changed.connect(
        lambda key, new, old: record("signal", key, new, old)
    )
    return events


def test_set_public_signature_stays_stable():
    signature = inspect.signature(Store.set)

    assert list(signature.parameters) == ["self", "key", "value", "force"]
    assert all(
        parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        for parameter in signature.parameters.values()
    )
    assert signature.parameters["force"].default is False
    assert get_type_hints(Store.set)["return"] is type(None)


def test_batch_delays_and_preserves_first_old_final_new_order(qapp):
    store = Store("batch-order")
    store.define("a", 0)
    store.define("b", 0)
    events = _attach_observers(store, "a", "b")

    with store.batch():
        store.set("a", 1)
        store.set("b", 2)
        store.set("a", 3)
        assert events == []
        assert store.values() == {"a": 3, "b": 2}

    expected_state = {"a": 3, "b": 2}
    assert events == [
        ("key", "a", 3, 0, expected_state),
        ("global", "a", 3, 0, expected_state),
        ("signal", "a", 3, 0, expected_state),
        ("key", "b", 2, 0, expected_state),
        ("global", "b", 2, 0, expected_state),
        ("signal", "b", 2, 0, expected_state),
    ]


def test_batch_missing_none_materializes_before_delayed_notification(qapp):
    store = Store("batch-missing-none")
    events = _attach_observers(store, "optional")

    with store.batch():
        store.set("optional", None)
        assert "optional" in store
        assert store.values() == {"optional": None}
        assert events == []

    assert events == [
        ("key", "optional", None, None, {"optional": None}),
        ("global", "optional", None, None, {"optional": None}),
        ("signal", "optional", None, None, {"optional": None}),
    ]


def test_batch_force_existing_none_records_one_change(qapp):
    store = Store("batch-force")
    store.define("optional", None)
    events = _attach_observers(store, "optional")

    with store.batch():
        store.set("optional", None, force=True)
        assert events == []

    assert [event[:4] for event in events] == [
        ("key", "optional", None, None),
        ("global", "optional", None, None),
        ("signal", "optional", None, None),
    ]
