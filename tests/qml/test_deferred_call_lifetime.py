# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""DeferredCall scheduling and lifetime contracts. DeferredCall 调度与生命周期契约。

Qt.callLater() 的回调由引擎排队，目标对象销毁不会取消它；回调执行时目标的 QML 上下文可能已
失效，Qt 会报 "attempted to evaluate a function in an invalid context"，并让该对象上的 QML 方法
解析成 undefined。DeferredCall 把待执行动作绑在宿主寿命上，本文件钉住以下契约：

1. 动作延迟到下一帧执行，不进同一调用栈；
2. 同一函数对象重复入队合并为一次，不同闭包各自执行；
3. coalesce 同一 key 只保留最后一次，cancel/cancelAll 可丢弃；
4. **委托类宿主被模型重置同步销毁时，待执行动作永不执行，也不产生 invalid context 警告**。

注意：QML 的 Object.destroy() 把实际删除推迟到事件循环（实测 0ms 定时器先于销毁执行），
因此寿命契约必须用「Repeater 委托 + 模型重置」这条真实同步销毁路径验证。
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl, Slot, qInstallMessageHandler
from PySide6.QtQml import QQmlComponent

ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "deferred-call.qml"))
SCENE = b"""
import QtQuick
import PrismQML as Fluent

Item {
    id: root

    property var sink: null

    function makeHost() {
        return hostComponent.createObject(root, { sink: root.sink })
    }

    function killHost(host) {
        host.destroy()
    }

    function addDelegate() {
        rows.append({ label: "row-" + rows.count })
    }

    function clearDelegates() {
        rows.clear()
    }

    function delegateCount() {
        return repeater.count
    }

    ListModel { id: rows }

    Repeater {
        id: repeater

        model: rows

        delegate: Item {
            id: delegateHost

            Component.onCompleted: {
                sink.delegateCreated()
                deferred.call(sink.delegateBump)
            }

            Component.onDestruction: sink.delegateDestroyed()

            Fluent.DeferredCall { id: deferred }
        }
    }

    Component {
        id: hostComponent

        Item {
            id: host

            property var sink: null

            function bumpOnce() {
                deferred.call(sink.bump)
            }

            function bumpTwiceWithCapturedAction() {
                var action = sink.bump
                deferred.call(action)
                deferred.call(action)
            }

            function bumpWithDistinctClosures() {
                deferred.call(function() { sink.bump() })
                deferred.call(function() { sink.bump() })
            }

            function coalesceValue(value) {
                deferred.coalesce("value", function() { sink.bumpValue(value) })
            }

            function cancelValue() {
                deferred.cancel("value")
            }

            function cancelAllPending() {
                deferred.cancelAll()
            }

            function pendingCount() {
                return deferred.pendingCount
            }

            Fluent.DeferredCall { id: deferred }
        }
    }
}
"""


class _Sink(QObject):
    """Stays alive across host destruction to observe deferred actions. 宿主销毁后仍在的观察者。"""

    def __init__(self) -> None:
        super().__init__()
        self.count = 0
        self.values: list[int] = []
        self.delegate_created = 0
        self.delegate_destroyed = 0
        self.delegate_bumps = 0

    @Slot()
    def bump(self) -> None:
        self.count += 1

    @Slot(int)
    def bumpValue(self, value: int) -> None:
        self.values.append(value)

    @Slot()
    def delegateCreated(self) -> None:
        self.delegate_created += 1

    @Slot()
    def delegateDestroyed(self) -> None:
        self.delegate_destroyed += 1

    @Slot()
    def delegateBump(self) -> None:
        self.delegate_bumps += 1


def _pump(qapp, milliseconds: int = 40) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()
    qapp.processEvents()


@contextmanager
def _capture_qt_messages() -> Iterator[list[str]]:
    messages: list[str] = []

    def handler(_mode, _context, message):
        messages.append(str(message))

    previous = qInstallMessageHandler(handler)
    try:
        yield messages
    finally:
        qInstallMessageHandler(previous)


def _create_scene(qml_engine, sink: _Sink):
    component = QQmlComponent(qml_engine)
    component.setData(SCENE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(qml_engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    root.setProperty("sink", sink)
    return component, root


def test_call_defers_to_next_tick_and_collapses_identical_functions(qml_engine, qapp):
    sink = _Sink()
    component, root = _create_scene(qml_engine, sink)
    host = root.makeHost()
    try:
        host.bumpOnce()
        assert sink.count == 0, "动作不得在入队的同一调用栈里执行"
        assert host.pendingCount() == 1

        _pump(qapp)
        assert sink.count == 1
        assert host.pendingCount() == 0

        host.bumpTwiceWithCapturedAction()
        _pump(qapp)
        assert sink.count == 2, "同一函数对象重复入队必须合并为一次"

        host.bumpWithDistinctClosures()
        _pump(qapp)
        assert sink.count == 4, "不同闭包必须各自执行"
    finally:
        root.deleteLater()
        qapp.processEvents()
        del component


def test_coalesce_keeps_latest_action_per_key(qml_engine, qapp):
    sink = _Sink()
    component, root = _create_scene(qml_engine, sink)
    host = root.makeHost()
    try:
        host.coalesceValue(1)
        host.coalesceValue(2)
        assert host.pendingCount() == 1

        _pump(qapp)
        assert sink.values == [2]
    finally:
        root.deleteLater()
        qapp.processEvents()
        del component


def test_cancel_and_cancel_all_drop_pending_actions(qml_engine, qapp):
    sink = _Sink()
    component, root = _create_scene(qml_engine, sink)
    host = root.makeHost()
    try:
        host.coalesceValue(7)
        host.cancelValue()
        assert host.pendingCount() == 0
        _pump(qapp)
        assert sink.values == []

        host.coalesceValue(8)
        host.cancelAllPending()
        _pump(qapp)
        assert sink.values == []
    finally:
        root.deleteLater()
        qapp.processEvents()
        del component


def test_repeater_delegate_teardown_drops_pending_actions(qml_engine, qapp):
    """模型重置同步销毁委托时，委托内待执行动作不得执行，也不得产生无效上下文警告。"""
    sink = _Sink()
    component, root = _create_scene(qml_engine, sink)
    try:
        with _capture_qt_messages() as messages:
            root.addDelegate()
            root.addDelegate()
            assert root.delegateCount() == 2
            assert sink.delegate_created == 2

            # 同一调用栈内清空模型：Repeater 同步销毁这两个委托（线上同款路径）
            root.clearDelegates()
            assert sink.delegate_destroyed == 2, "Repeater 必须同步销毁委托"
            assert root.delegateCount() == 0

            _pump(qapp, 60)
            assert sink.delegate_bumps == 0, "宿主销毁后待执行动作不得执行"

            # 新建的委托仍须正常延迟执行（本原语没有全局状态残留）。
            root.addDelegate()
            _pump(qapp, 60)
            assert sink.delegate_bumps == 1
            assert sink.delegate_created == 3

        noisy = [
            message
            for message in messages
            if "invalid context" in message or "is not a function" in message
        ]
        assert not noisy, noisy
    finally:
        root.deleteLater()
        qapp.processEvents()
        del component
