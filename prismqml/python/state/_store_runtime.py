# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Store runtime adapters. Store 运行时适配器。"""

from __future__ import annotations

from threading import RLock
from typing import Any, Callable, Optional, TYPE_CHECKING
from weakref import ref

from PySide6.QtCore import QObject, Property, Qt, Signal, Slot

if TYPE_CHECKING:
    from .store import Store


class StoreThreadError(RuntimeError):
    """Raised when a Store owner-thread contract is violated. Store 线程契约被违反时抛出。"""


class StoreSubscription:
    """Idempotent watcher handle. 可幂等关闭的 watcher 订阅句柄。"""

    def __init__(self, cancel: Callable[[], None]):
        self._cancel = cancel
        self._closed = False
        self._lock = RLock()

    @property
    def closed(self) -> bool:
        """Whether this subscription has been cancelled. 是否已取消。"""
        with self._lock:
            return self._closed

    def close(self) -> None:
        """Cancel the watcher once. 只取消 watcher 一次。"""
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self._cancel()

    def __call__(self) -> None:
        """Keep compatibility with the former callable unwatch API. 兼容旧的可调用取消 API。"""
        self.close()


class StoreDispatcher(QObject):
    """Queue work onto the Store owner's Qt thread. 将工作排队到 Store 所属 Qt 线程。"""

    invokeRequested = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.invokeRequested.connect(self._execute, Qt.QueuedConnection)

    @Slot(object)
    def _execute(self, operation: Callable[[], None]) -> None:
        """Execute one queued operation on the receiver thread. 在接收者线程执行任务。"""
        operation()


class StoreBinding(QObject):
    """A bindable QML view of one Store key. 一个 Store 键的可绑定 QML 视图。"""

    valueChanged = Signal()

    def __init__(self, store: "Store", key: str, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._store = store
        self._key = key
        binding_ref = ref(self)

        def on_store_changed(new_value: Any, old_value: Any) -> None:
            binding = binding_ref()
            if binding is not None:
                binding._on_store_changed(new_value, old_value)

        self._subscription = store.watch(key, on_store_changed, owner=self)

    @Property(str, constant=True)
    def key(self) -> str:
        """Return the bound key. 返回绑定的键。"""
        return self._key

    @Property(object, notify=valueChanged)
    def value(self) -> Any:
        """Read the current value. 读取当前值。"""
        return self._store.get(self._key)

    @value.setter
    def value(self, value: Any) -> None:
        """Write the value through the owner-thread Store API. 通过所属线程 Store API 写入。"""
        self._store.set(self._key, value)

    @Slot()
    def close(self) -> None:
        """Stop observing this key. 停止观察该键。"""
        self._subscription.close()

    def _on_store_changed(self, _new_value: Any, _old_value: Any) -> None:
        """Notify QML after the Store value changed. Store 变化后通知 QML。"""
        self.valueChanged.emit()


class StoreObject(QObject):
    """QML-facing Store facade with stable per-key bindings. 面向 QML 的 Store 门面。"""

    changed = Signal(str, object, object)

    def __init__(self, store: "Store", parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        store.assert_owner_thread()
        self._store = store
        self._store.qt_signals.changed.connect(self._forward_changed)

    @Property(str, constant=True)
    def name(self) -> str:
        """Return the Store name. 返回 Store 名称。"""
        return self._store.name

    @Slot(str, result=QObject)
    def binding(self, key: str) -> StoreBinding:
        """Return a stable bindable object for one key. 返回指定键的稳定绑定对象。"""
        return self._store.bind(key)

    @Slot(str, result=object)
    def value(self, key: str) -> Any:
        """Read a value from QML. 从 QML 读取值。"""
        return self._store.get(key)

    @Slot(str, object, result=bool)
    def setValue(self, key: str, value: Any) -> bool:
        """Set a value from QML and report success. 从 QML 写入并返回成功状态。"""
        self._store.set(key, value)
        return True

    @Slot(result="QVariantMap")
    def snapshot(self) -> dict[str, Any]:
        """Return a point-in-time state copy. 返回当前状态副本。"""
        return self._store.values()

    def _forward_changed(self, key: str, new_value: Any, old_value: Any) -> None:
        """Forward Store notifications to QML Connections. 转发 Store 通知给 QML Connections。"""
        self.changed.emit(key, new_value, old_value)
