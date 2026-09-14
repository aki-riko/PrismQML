# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""PrismQML Store - thread-confined reactive state. 线程约束的响应式状态存储。"""

from __future__ import annotations

from collections import deque
from concurrent.futures import Future
from threading import RLock, get_ident
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple

from PySide6.QtCore import QCoreApplication, QObject, QThread, Signal

from ..core.logger import exception
from ._store_runtime import (
    StoreBinding,
    StoreDispatcher,
    StoreObject,
    StoreSubscription,
    StoreThreadError,
)


def _log_watcher_failure(
    store_name: str, key: str, exc: Exception, *, global_watcher: bool
) -> None:
    """Log one isolated user watcher failure. 记录一次已隔离的用户回调失败。"""
    label = "Global watcher" if global_watcher else "Watcher"
    exception(
        f"[Store:{store_name}] {label} error for '{key}': "
        f"{type(exc).__name__}: {exc}"
    )


class StoreSignals(QObject):
    """Store 的 Qt 信号桥接。"""

    changed = Signal(str, object, object)  # key, new_value, old_value


class Store:
    """响应式状态存储，通知严格归属创建它的 Qt 线程。

    ``set``、``define``、``watch`` 和批处理只能在创建 Store 的线程调用。
    后台线程必须使用 ``post_set``；该方法通过 Qt queued Signal 将更新按提交
    顺序送回 Store 线程。这样 Python watcher、Qt signal 和 QML binding 不会
    在 worker 线程执行。
    """

    def __init__(self, name: str = ""):
        """初始化 Store 并记录其 Qt 所属线程。"""
        self._name = name or self.__class__.__name__
        self._owner_thread = QThread.currentThread()
        self._owner_python_thread_id = get_ident()
        self._lock = RLock()
        self._state: Dict[str, Any] = {}
        self._defaults: Dict[str, Any] = {}
        self._watchers: Dict[str, List[Callable[[Any, Any], None]]] = {}
        self._global_watchers: List[Callable[[str, Any, Any], None]] = []
        self._batch_mode = False
        self._batch_depth = 0
        self._batch_changes: Dict[str, Tuple[Any, Any]] = {}
        self._signals = StoreSignals()
        # QML keeps a C++ pointer to this object; retain the Python wrapper until close().
        # QML 只保留 C++ 指针，因此必须保留 Python wrapper 到 Store 关闭。
        self._bindings: Dict[str, StoreBinding] = {}
        self._dispatcher = StoreDispatcher()
        self._post_lock = RLock()
        self._post_queue: Deque[Tuple[Future, str, Any, bool]] = deque()
        self._post_scheduled = False
        self._closed = False

    @property
    def name(self) -> str:
        """获取 Store 名称。"""
        return self._name

    @property
    def qt_signals(self) -> StoreSignals:
        """获取 Qt 信号对象，用于 QML 或 Qt 连接。"""
        return self._signals

    @property
    def owner_thread(self) -> QThread:
        """Return the Qt thread that owns this Store. 返回 Store 所属 Qt 线程。"""
        return self._owner_thread

    def is_owner_thread(self) -> bool:
        """Return whether the caller is on the Store thread. 判断当前调用线程。"""
        return get_ident() == self._owner_python_thread_id

    def assert_owner_thread(self) -> None:
        """Reject unsafe direct access from another thread. 拒绝跨线程直接访问。"""
        if not self.is_owner_thread():
            raise StoreThreadError(
                f"Store '{self._name}' must be accessed from its owner Qt thread"
            )

    def define(self, key: str, default: Any = None) -> None:
        """定义状态字段（用于继承模式）。"""
        self.assert_owner_thread()
        with self._lock:
            self._ensure_open()
            self._defaults[key] = default
            if key not in self._state:
                self._state[key] = default

    def get(self, key: str, default: Any = None) -> Any:
        """获取状态值；读取可从任意线程安全执行。"""
        with self._lock:
            if key in self._state:
                return self._state[key]
            if key in self._defaults:
                return self._defaults[key]
            return default

    def set(self, key: str, value: Any, force: bool = False) -> None:
        """设置状态值并在 Store 线程通知订阅者。"""
        self.assert_owner_thread()
        notify_now = False
        with self._lock:
            self._ensure_open()
            old = self._state.get(key)
            if not force and key in self._state and old == value:
                return
            self._state[key] = value
        if self._batch_mode:
            self._record_batch_change(key, value, old)
        else:
            notify_now = True
        if notify_now:
            self._notify(key, value, old)

    def post_set(
        self, key: str, value: Any, force: bool = False
    ) -> Future:
        """Queue a cross-thread update and return its completion Future. 排队跨线程更新。"""
        future: Future = Future()
        if self.is_owner_thread():
            self._complete_posted_set(future, key, value, force)
            return future
        error = self._post_set_preflight()
        if error is not None:
            future.set_exception(error)
            return future
        self._enqueue_posted(future, key, value, force)
        return future

    def bind(self, key: str) -> StoreBinding:
        """Return one stable bindable object for a key. 返回指定键的稳定绑定对象。"""
        self.assert_owner_thread()
        binding = self._bindings.get(key)
        if binding is None:
            binding = StoreBinding(self, key)
            self._bindings[key] = binding
        return binding

    def as_qml(self, parent: Optional[QObject] = None) -> StoreObject:
        """Create the QML facade. 创建面向 QML 的 Store 门面。"""
        return StoreObject(self, parent)

    def _record_batch_change(self, key: str, value: Any, old: Any) -> None:
        """Record one delayed batch notification. 记录一项延迟批处理通知。"""
        if key not in self._batch_changes:
            self._batch_changes[key] = (value, old)
            return
        _, original_old = self._batch_changes[key]
        self._batch_changes[key] = (value, original_old)

    def _notify(self, key: str, new_value: Any, old_value: Any) -> None:
        """Notify all observers in a stable order on the owner thread。"""
        self.assert_owner_thread()
        with self._lock:
            if self._closed:
                return
            key_watchers = list(self._watchers.get(key, ()))
            global_watchers = list(self._global_watchers)

        for callback in key_watchers:
            try:
                callback(new_value, old_value)
            except Exception as exc:
                _log_watcher_failure(self._name, key, exc, global_watcher=False)

        for callback in global_watchers:
            try:
                callback(key, new_value, old_value)
            except Exception as exc:
                _log_watcher_failure(self._name, key, exc, global_watcher=True)

        self._signals.changed.emit(key, new_value, old_value)

    def watch(
        self,
        key: str,
        callback: Callable[[Any, Any], None],
        *,
        owner: Optional[QObject] = None,
    ) -> StoreSubscription:
        """监听指定 key，并可绑定 QObject 生命周期。"""
        self.assert_owner_thread()
        if not callable(callback):
            raise TypeError("callback must be callable")
        with self._lock:
            self._ensure_open()
            self._watchers.setdefault(key, []).append(callback)

        def cancel() -> None:
            with self._lock:
                callbacks = self._watchers.get(key)
                if callbacks is not None and callback in callbacks:
                    callbacks.remove(callback)
                    if not callbacks:
                        self._watchers.pop(key, None)

        subscription = StoreSubscription(cancel)
        if owner is not None:
            self._attach_owner(subscription, owner)
        return subscription

    def watch_all(
        self,
        callback: Callable[[str, Any, Any], None],
        *,
        owner: Optional[QObject] = None,
    ) -> StoreSubscription:
        """监听所有状态变化，并可绑定 QObject 生命周期。"""
        self.assert_owner_thread()
        if not callable(callback):
            raise TypeError("callback must be callable")
        with self._lock:
            self._ensure_open()
            self._global_watchers.append(callback)

        def cancel() -> None:
            with self._lock:
                if callback in self._global_watchers:
                    self._global_watchers.remove(callback)

        subscription = StoreSubscription(cancel)
        if owner is not None:
            self._attach_owner(subscription, owner)
        return subscription

    def batch(self) -> "BatchContext":
        """开始可嵌套批量更新（退出最外层时统一通知）。"""
        return BatchContext(self)

    def reset(self, key: Optional[str] = None) -> None:
        """重置状态到默认值。"""
        self.assert_owner_thread()
        with self._lock:
            defaults = (
                ((key, self._defaults[key]),)
                if key is not None and key in self._defaults
                else tuple(self._defaults.items()) if key is None else ()
            )
        for reset_key, value in defaults:
            self.set(reset_key, value)

    def close(self) -> None:
        """Stop accepting updates and detach all observers. 关闭 Store 并解除观察者。"""
        self.assert_owner_thread()
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._watchers.clear()
            self._global_watchers.clear()
            self._batch_changes.clear()
            self._batch_depth = 0
            self._batch_mode = False
        with self._post_lock:
            pending = list(self._post_queue)
            self._post_queue.clear()
            self._post_scheduled = False
        close_error = StoreThreadError("Store is closed")
        for future, _key, _value, _force in pending:
            if not future.done():
                future.set_exception(close_error)
        bindings = tuple(self._bindings.values())
        self._bindings.clear()
        for binding in bindings:
            binding.close()

    def keys(self) -> List[str]:
        """获取所有状态键。"""
        with self._lock:
            return list(self._state.keys())

    def values(self) -> Dict[str, Any]:
        """获取所有状态值（浅副本）。"""
        with self._lock:
            return dict(self._state)

    def __getitem__(self, key: str) -> Any:
        """支持 store["key"] 语法。"""
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """支持 store["key"] = value 语法。"""
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        """支持 key in store 语法。"""
        with self._lock:
            return key in self._state

    def _ensure_open(self) -> None:
        if self._closed:
            raise StoreThreadError("Store is closed")

    def _complete_posted_set(
        self, future: Future, key: str, value: Any, force: bool
    ) -> None:
        try:
            self.set(key, value, force)
        except BaseException as exc:
            future.set_exception(exc)
        else:
            future.set_result(None)

    def _post_set_preflight(self) -> Optional[StoreThreadError]:
        """Validate that the owner thread can receive queued work. 校验 Store 线程可接收排队任务。"""
        if QCoreApplication.instance() is None:
            return StoreThreadError("post_set requires a running QCoreApplication")
        if self._owner_thread.eventDispatcher() is None:
            return StoreThreadError("Store owner thread has no Qt event dispatcher")
        with self._post_lock:
            if self._closed:
                return StoreThreadError("Store is closed")
        return None

    def _enqueue_posted(
        self, future: Future, key: str, value: Any, force: bool
    ) -> None:
        """Append one update and schedule one drain signal. 添加更新并安排一次排空信号。"""
        should_schedule = False
        with self._post_lock:
            if self._closed:
                future.set_exception(StoreThreadError("Store is closed"))
                return
            self._post_queue.append((future, key, value, force))
            if not self._post_scheduled:
                self._post_scheduled = True
                should_schedule = True
        if not should_schedule:
            return
        try:
            self._dispatcher.invokeRequested.emit(self._drain_posted)
        except BaseException as exc:
            self._fail_posted(exc)

    def _attach_owner(self, subscription: StoreSubscription, owner: QObject) -> None:
        """Tie a subscription to a same-thread QObject lifetime. 绑定同线程 QObject 生命周期。"""
        if owner.thread() != QThread.currentThread():
            subscription.close()
            raise StoreThreadError("watch owner must share the Store Qt thread")

        def cancel_on_destroyed(*_args: Any) -> None:
            subscription.close()

        owner.destroyed.connect(cancel_on_destroyed)

    def _drain_posted(self) -> None:
        """Drain the FIFO queue on the Store owner thread. 在 Store 线程排空 FIFO 队列。"""
        self.assert_owner_thread()
        while True:
            with self._post_lock:
                if not self._post_queue:
                    self._post_scheduled = False
                    return
                future, key, value, force = self._post_queue.popleft()
            self._complete_posted_set(future, key, value, force)

    def _fail_posted(self, error: BaseException) -> None:
        with self._post_lock:
            pending = list(self._post_queue)
            self._post_queue.clear()
            self._post_scheduled = False
        for future, _key, _value, _force in pending:
            if not future.done():
                future.set_exception(error)


class BatchContext:
    """可嵌套批量更新上下文。"""

    def __init__(self, store: Store):
        self._store = store

    def __enter__(self) -> "BatchContext":
        self._store.assert_owner_thread()
        with self._store._lock:
            self._store._ensure_open()
            self._store._batch_depth += 1
            self._store._batch_mode = True
            if self._store._batch_depth == 1:
                self._store._batch_changes.clear()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        self._store.assert_owner_thread()
        with self._store._lock:
            self._store._batch_depth -= 1
            if self._store._batch_depth > 0:
                return False
            self._store._batch_mode = False
            changes = tuple(self._store._batch_changes.items())
            self._store._batch_changes.clear()
        for key, (new_value, old_value) in changes:
            self._store._notify(key, new_value, old_value)
        return False
