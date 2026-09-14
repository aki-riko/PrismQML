# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Store threading and QML contracts. Store 线程与 QML 合同测试。"""

from __future__ import annotations

import threading
import time
import gc
import weakref

import pytest
import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QThread, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

from prismqml import Store, StoreThreadError


def _pump_until(qapp, predicate, timeout=2.0):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        qapp.processEvents(QEventLoop.AllEvents, 10)
        time.sleep(0.001)
    return predicate()


def test_direct_cross_thread_set_is_rejected(qapp):
    store = Store("thread-contract")
    errors = []

    def worker():
        try:
            store.set("value", 1)
        except Exception as exc:
            errors.append(exc)

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(timeout=1)

    assert not thread.is_alive()
    assert len(errors) == 1
    assert isinstance(errors[0], StoreThreadError)
    assert "owner Qt thread" in str(errors[0])
    assert store.get("value") is None


def test_qml_facade_rejects_parent_from_another_thread(qapp):
    store = Store("qml-parent-contract")

    class ForeignParent:
        def thread(self):
            return QThread()

    with pytest.raises(StoreThreadError, match="parent must share"):
        store.as_qml(ForeignParent())


def test_post_set_is_fifo_and_notifies_on_owner_thread(qapp):
    store = Store("thread-queue")
    events = []
    store.define("value", 0)
    store.watch(
        "value",
        lambda new, old: events.append(
            (new, old, QThread.currentThread() == store.owner_thread)
        ),
    )
    futures = []

    def worker():
        for value in (1, 2, 3):
            futures.append(store.post_set("value", value))

    thread = threading.Thread(target=worker)
    thread.start()
    assert _pump_until(qapp, lambda: not thread.is_alive())
    thread.join(timeout=1)
    assert _pump_until(qapp, lambda: all(future.done() for future in futures))

    assert [future.result() for future in futures] == [None, None, None]
    assert events == [(1, 0, True), (2, 1, True), (3, 2, True)]
    assert store.get("value") == 3


def test_cancelled_post_set_does_not_break_following_updates(qapp):
    store = Store("cancelled-queue")
    store.define("value", 0)
    events = []
    store.watch("value", lambda new, old: events.append((new, old)))
    futures = []
    submitted = threading.Event()
    release = threading.Event()

    def worker():
        futures.append(store.post_set("value", 1))
        futures.append(store.post_set("value", 2))
        submitted.set()
        release.wait(timeout=1)

    thread = threading.Thread(target=worker)
    thread.start()
    assert submitted.wait(timeout=1)
    assert futures[0].cancel()
    release.set()
    assert _pump_until(qapp, lambda: not thread.is_alive())
    thread.join(timeout=1)
    assert _pump_until(qapp, lambda: futures[1].done())

    assert futures[0].cancelled()
    assert futures[1].result() is None
    assert events == [(1, 0), (2, 1)]
    assert store.get("value") == 2


def test_post_set_completion_race_with_cancel_does_not_raise(qapp):
    store = Store("cancel-race")
    store.define("value", 0)
    futures = []
    submitted = threading.Event()

    def worker():
        future = store.post_set("value", 1)
        original_set_result = future.set_result

        def cancel_before_completion(result):
            future.cancel()
            return original_set_result(result)

        future.set_result = cancel_before_completion
        futures.append(future)
        futures.append(store.post_set("value", 2))
        submitted.set()

    thread = threading.Thread(target=worker)
    thread.start()
    assert submitted.wait(timeout=1)
    thread.join(timeout=1)
    assert not thread.is_alive()
    assert _pump_until(qapp, lambda: futures[1].done())

    assert futures[0].cancelled()
    assert futures[1].result() is None
    assert store.get("value") == 2


def test_post_set_queue_is_sliced_for_large_bursts(qapp):
    store = Store("burst-queue")
    store.define("value", 0)
    events = []
    store.watch("value", lambda new, old: events.append((new, old)))
    futures = []

    def worker():
        for value in range(1, 130):
            futures.append(store.post_set("value", value))

    thread = threading.Thread(target=worker)
    thread.start()
    assert _pump_until(qapp, lambda: not thread.is_alive())
    thread.join(timeout=1)
    assert _pump_until(qapp, lambda: all(future.done() for future in futures))

    assert len(events) == 129
    assert events[0] == (1, 0)
    assert events[-1] == (129, 128)
    assert store.get("value") == 129


def test_nested_batch_flushes_once_in_first_change_order(qapp):
    store = Store("nested-batch")
    events = []
    store.define("first", 0)
    store.define("second", 0)
    store.watch_all(lambda key, new, old: events.append((key, new, old)))

    with store.batch():
        store.set("first", 1)
        with store.batch():
            store.set("second", 2)
            store.set("first", 3)
        assert events == []

    assert events == [("first", 3, 0), ("second", 2, 0)]


def test_batch_context_rejects_repeated_exit_without_corrupting_store(qapp):
    store = Store("batch-context-lifecycle")
    context = store.batch()
    context.__enter__()
    context.__exit__(None, None, None)

    with pytest.raises(RuntimeError, match="without being entered"):
        context.__exit__(None, None, None)

    events = []
    store.define("value", 0)
    store.watch("value", lambda new, old: events.append((new, old)))
    with store.batch():
        store.set("value", 1)
    assert events == [(1, 0)]


def test_owner_destruction_cancels_subscription(qapp):
    store = Store("owner-lifecycle")
    store.define("value", 0)
    owner = QObject()
    events = []
    store.watch("value", lambda new, old: events.append((new, old)), owner=owner)

    owner.deleteLater()
    QCoreApplication.sendPostedEvents(owner, QEvent.Type.DeferredDelete)
    store.set("value", 1)

    assert events == []


def test_closed_owner_subscription_releases_callback_and_signal_connection(qapp):
    store = Store("owner-cleanup")
    owner = QObject()

    def callback(_new, _old):
        return None

    callback_ref = weakref.ref(callback)
    subscription = store.watch("value", callback, owner=owner)
    subscription.close()
    del callback
    gc.collect()

    assert callback_ref() is None


def test_batch_context_exit_after_store_close_does_not_underflow(qapp):
    store = Store("batch-close")
    context = store.batch()
    context.__enter__()
    store.close()

    context.__exit__(None, None, None)

    assert store._batch_depth == 0
    assert store._batch_mode is False


def test_close_fails_queued_updates_without_touching_state(qapp):
    store = Store("close-queue")
    store.define("value", 0)
    started = threading.Event()
    result = []

    def worker():
        future = store.post_set("value", 1)
        started.set()
        result.append(future)

    thread = threading.Thread(target=worker)
    thread.start()
    assert started.wait(timeout=1)
    store.close()
    thread.join(timeout=1)

    assert not thread.is_alive()
    assert result[0].done()
    with pytest.raises(StoreThreadError, match="closed"):
        result[0].result()
    assert store.get("value") == 0


def test_qml_binding_and_connections_receive_owner_thread_updates(qapp):
    store = Store("qml-store")
    store.define("count", 0)
    qml_store = store.as_qml()
    engine = QQmlEngine()
    engine.rootContext().setContextProperty("appStore", qml_store)
    component = QQmlComponent(engine)
    component.setData(
        b"""
        import QtQml
        import QtQuick
        Item {
            property var observed: appStore.binding("count").value
            property int signalCount: 0
            property string lastKey: ""
            property var lastValue: undefined
            Connections {
                target: appStore
                function onChanged(key, newValue, oldValue) {
                    signalCount += 1
                    lastKey = key
                    lastValue = newValue
                }
            }
        }
        """,
        QUrl("inline:store-binding.qml"),
    )
    assert _pump_until(
        qapp, lambda: component.status() != QQmlComponent.Status.Loading
    )
    assert not component.isError(), [error.toString() for error in component.errors()]
    root = component.create()
    assert root is not None
    assert root.property("observed") == 0

    store.set("count", 7)
    qapp.processEvents(QEventLoop.AllEvents, 20)

    assert root.property("observed") == 7
    assert root.property("signalCount") == 1
    assert root.property("lastKey") == "count"
    assert root.property("lastValue") == 7

    binding = store.bind("count")
    assert shiboken6.isValid(binding)
    assert store.bind("count") is binding

    root.deleteLater()
    qml_store.deleteLater()
    engine.deleteLater()
    qapp.processEvents(QEventLoop.AllEvents, 20)


def test_qml_facade_is_retained_when_passed_without_python_reference(qapp):
    store = Store("qml-facade-lifetime")
    store.define("count", 3)
    engine = QQmlEngine()
    engine.rootContext().setContextProperty("appStore", store.as_qml())
    gc.collect()
    component = QQmlComponent(engine)
    component.setData(
        b"""
        import QtQuick
        Item { property var observed: appStore.binding(\"count\").value }
        """,
        QUrl("inline:store-facade-lifetime.qml"),
    )
    assert _pump_until(
        qapp, lambda: component.status() != QQmlComponent.Status.Loading
    )
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create()

    assert root is not None
    assert root.property("observed") == 3

    root.deleteLater()
    engine.deleteLater()
    qapp.processEvents(QEventLoop.AllEvents, 20)
