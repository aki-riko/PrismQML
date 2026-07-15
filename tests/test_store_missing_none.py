# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Store missing-key None regressions. Store 缺键 None 回归。"""

import pytest

from prismqml import Store


class _ExplosiveEquality:
    def __eq__(self, _other):
        raise AssertionError("missing values must not be compared")


class _RaisingEquality:
    def __init__(self, error):
        self._error = error

    def __eq__(self, _other):
        raise self._error


def _record_notifications(store, key):
    events = []

    def record(label, event_key, new, old):
        events.append(
            (label, event_key, new, old, key in store, store.values())
        )

    store.watch(key, lambda new, old: record("key", key, new, old))
    store.watch_all(lambda changed, new, old: record("global", changed, new, old))
    store.qt_signals.changed.connect(
        lambda changed, new, old: record("signal", changed, new, old)
    )
    return events


def test_missing_none_inserts_before_ordered_notifications(qapp):
    store = Store("missing-none")
    events = _record_notifications(store, "optional")

    store.set("optional", None)

    assert "optional" in store
    assert store.keys() == ["optional"]
    assert store.values() == {"optional": None}
    assert [event[0] for event in events] == ["key", "global", "signal"]
    for label, key, new, old, present, values in events:
        assert label in {"key", "global", "signal"}
        assert (key, new, old) == ("optional", None, None)
        assert present is True
        assert values == {"optional": None}


def test_existing_none_skips_unless_forced(qapp):
    store = Store("existing-none")
    events = _record_notifications(store, "optional")
    store.set("optional", None, force=True)
    events.clear()

    store.set("optional", None)
    assert events == []

    store.set("optional", None, force=True)
    assert [event[0] for event in events] == ["key", "global", "signal"]


def test_dict_assignment_creates_missing_none_key(qapp):
    store = Store("dict-none")

    store["optional"] = None

    assert "optional" in store
    assert store.values() == {"optional": None}


def test_missing_value_does_not_run_synthetic_old_equality(qapp):
    store = Store("missing-equality")
    value = _ExplosiveEquality()

    store.set("payload", value)

    assert store.get("payload") is value


def test_defined_none_remains_an_existing_equal_value(qapp):
    store = Store("defined-none")
    store.define("optional", None)
    events = _record_notifications(store, "optional")

    store.set("optional", None)

    assert events == []
    assert store.values() == {"optional": None}


@pytest.mark.parametrize("error_type", (RuntimeError, KeyboardInterrupt, SystemExit))
def test_existing_equality_failure_and_force_contract_stay_unchanged(
    qapp, error_type
):
    store = Store("existing-equality")
    failure = error_type("eq failed")
    old = _RaisingEquality(failure)
    store.set("payload", old, force=True)
    events = _record_notifications(store, "payload")

    with pytest.raises(error_type) as caught:
        store.set("payload", object())

    assert caught.value is failure
    assert store.get("payload") is old
    assert events == []
    replacement = object()
    store.set("payload", replacement, force=True)
    assert store.get("payload") is replacement
    assert [event[0] for event in events] == ["key", "global", "signal"]
