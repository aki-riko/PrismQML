# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Store.set batching contracts. Store.set 批处理合同。"""

import ast
import inspect
import textwrap
from typing import get_type_hints

from prismqml import Store


def _method_node(method):
    lines, _start_line = inspect.getsourcelines(method)
    node = ast.parse(
        textwrap.dedent("".join(lines)), feature_version=(3, 9)
    ).body[0]
    assert isinstance(node, ast.FunctionDef)
    return lines, node


def _batch_mode_if(set_node):
    matches = [
        node
        for node in set_node.body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Attribute)
        and isinstance(node.test.value, ast.Name)
        and node.test.value.id == "self"
        and node.test.attr == "_batch_mode"
    ]
    assert len(matches) == 1
    return matches[0]


def _record_batch_calls(set_node):
    return [
        node
        for node in ast.walk(set_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "self"
        and node.func.attr == "_record_batch_change"
    ]


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


def test_set_delegates_batch_recording_to_small_helper():
    set_lines, set_node = _method_node(Store.set)
    helper_lines, _helper_node = _method_node(Store._record_batch_change)
    batch_if = _batch_mode_if(set_node)
    calls = _record_batch_calls(set_node)

    assert len(set_lines) <= 30
    assert len(helper_lines) <= 30
    assert len(calls) == 1
    assert len(batch_if.body) == 1
    assert isinstance(batch_if.body[0], ast.Expr)
    assert batch_if.body[0].value is calls[0]
    assert [argument.id for argument in calls[0].args] == ["key", "value", "old"]
    assert calls[0].keywords == []
    assert not any(
        isinstance(node, ast.Attribute) and node.attr == "_batch_changes"
        for node in ast.walk(set_node)
    )


def test_batch_delays_and_preserves_first_old_final_new_order(qapp):
    store = Store("batch-order")
    store.define("z", 0)
    store.define("a", 0)
    events = _attach_observers(store, "z", "a")

    with store.batch():
        store.set("z", 1)
        store.set("a", 2)
        store.set("z", 3)
        assert events == []
        assert store.values() == {"z": 3, "a": 2}

    expected_state = {"z": 3, "a": 2}
    assert events == [
        ("key", "z", 3, 0, expected_state),
        ("global", "z", 3, 0, expected_state),
        ("signal", "z", 3, 0, expected_state),
        ("key", "a", 2, 0, expected_state),
        ("global", "a", 2, 0, expected_state),
        ("signal", "a", 2, 0, expected_state),
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


def test_batch_force_existing_equal_value_records_one_change(qapp):
    for value in (None, 7):
        store = Store(f"batch-force-{value}")
        store.define("optional", value)
        events = _attach_observers(store, "optional")

        with store.batch():
            store.set("optional", value, force=True)
            assert events == []

        assert [event[:4] for event in events] == [
            ("key", "optional", value, value),
            ("global", "optional", value, value),
            ("signal", "optional", value, value),
        ]


def test_batch_preserves_none_and_object_identities(qapp):
    store = Store("batch-identities")
    original = object()
    intermediate = object()
    final = object()
    empty_value = object()
    store.define("empty", None)
    store.define("payload", original)
    events = _attach_observers(store, "empty", "payload")

    with store.batch():
        store.set("empty", empty_value)
        store.set("payload", intermediate)
        store.set("payload", final)

    assert [event[1] for event in events] == ["empty"] * 3 + ["payload"] * 3
    for _label, key, new, old, state in events:
        assert new is (empty_value if key == "empty" else final)
        assert old is (None if key == "empty" else original)
        assert state["empty"] is empty_value
        assert state["payload"] is final
