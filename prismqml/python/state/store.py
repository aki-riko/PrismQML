# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
"""FluentQML Store - 响应式状态存储

核心特性：
- 细粒度订阅：watch 特定 key，不会收到无关通知
- 批量更新：batch 模式下合并通知
- 计算属性：computed 自动依赖追踪
- 类型安全：可选的类型约束

设计理念：
- 比 EventBus 更清晰、更可控
- 状态变化可追踪、可调试
- 与 Qt Signal/Slot 兼容
"""

from typing import Any, Callable, Dict, List, Optional
from PySide6.QtCore import QObject, Signal
from ..core.logger import warning


class StoreSignals(QObject):
    """Store 的 Qt 信号桥接"""

    changed = Signal(str, object, object)  # key, new_value, old_value


class Store:
    """响应式状态存储基类

    使用示例：
        # 继承模式
        class SettingStore(Store):
            def __init__(self):
                super().__init__()
                self.define("theme", "auto")
                self.define("gpu", False)

        settingStore = SettingStore()
        settingStore.watch("theme", lambda new, old: print(f"主题: {old} -> {new}"))
        settingStore.set("theme", "dark")  # 触发回调

        # 直接实例化
        store = Store()
        store.set("count", 0)
        store.set("count", store.get("count") + 1)
    """

    def __init__(self, name: str = ""):
        """初始化 Store

        Args:
            name: Store 名称，用于调试
        """
        self._name = name or self.__class__.__name__
        self._state: Dict[str, Any] = {}
        self._defaults: Dict[str, Any] = {}
        self._watchers: Dict[str, List[Callable[[Any, Any], None]]] = {}
        self._global_watchers: List[Callable[[str, Any, Any], None]] = []
        self._batch_mode = False
        self._batch_changes: Dict[str, tuple] = {}  # key -> (new, old)
        self._signals = StoreSignals()

    @property
    def name(self) -> str:
        """获取 Store 名称"""
        return self._name

    @property
    def qt_signals(self) -> StoreSignals:
        """获取 Qt 信号对象，用于 QML 绑定"""
        return self._signals

    def define(self, key: str, default: Any = None) -> None:
        """定义状态字段（用于继承模式）

        Args:
            key: 状态键
            default: 默认值
        """
        self._defaults[key] = default
        if key not in self._state:
            self._state[key] = default

    def get(self, key: str, default: Any = None) -> Any:
        """获取状态值

        Args:
            key: 状态键
            default: 默认值（如果未定义）

        Returns:
            状态值
        """
        if key in self._state:
            return self._state[key]
        if key in self._defaults:
            return self._defaults[key]
        return default

    def set(self, key: str, value: Any, force: bool = False) -> None:
        """设置状态值（自动通知订阅者）

        Args:
            key: 状态键
            value: 新值
            force: 强制通知（即使值相同）。适用于原地修改可变对象后需要触发通知的场景。

        Note:
            使用 ``==`` 比较新旧值。如果 value 是可变对象（如 list/dict），
            原地修改后再 set() 回去不会触发通知（因为 old 和 value 指向同一对象）。
            推荐做法：总是传入新对象，如 ``store.set("items", items.copy())``，
            或使用 ``force=True`` 强制触发通知。
        """
        old = self._state.get(key)

        # 值相同则跳过（除非 force=True）
        if not force and old == value:
            return

        self._state[key] = value

        if self._batch_mode:
            # 批量模式：记录变化，稍后统一通知
            if key not in self._batch_changes:
                self._batch_changes[key] = (value, old)
            else:
                # 保留最早的 old 值
                _, original_old = self._batch_changes[key]
                self._batch_changes[key] = (value, original_old)
        else:
            # 立即通知
            self._notify(key, value, old)

    def _notify(self, key: str, new_value: Any, old_value: Any) -> None:
        """通知订阅者

        Args:
            key: 状态键
            new_value: 新值
            old_value: 旧值
        """
        # 通知特定 key 的订阅者 Notify key-specific watchers
        if key in self._watchers:
            for callback in self._watchers[key][:]:  # 复制列表防止迭代时修改
                try:
                    callback(new_value, old_value)
                except Exception as e:
                    warning(f"[Store:{self._name}] Watcher error for '{key}': {e}")

        # 通知全局订阅者 Notify global watchers
        for callback in self._global_watchers[:]:
            try:
                callback(key, new_value, old_value)
            except Exception as e:
                warning(f"[Store:{self._name}] Global watcher error: {e}")

        # 发送 Qt 信号
        self._signals.changed.emit(key, new_value, old_value)

    def watch(
        self, key: str, callback: Callable[[Any, Any], None]
    ) -> Callable[[], None]:
        """监听特定 key 的变化

        Args:
            key: 要监听的状态键
            callback: 回调函数 (new_value, old_value) -> None

        Returns:
            取消监听的函数
        """
        if key not in self._watchers:
            self._watchers[key] = []

        self._watchers[key].append(callback)

        def unwatch():
            if key in self._watchers and callback in self._watchers[key]:
                self._watchers[key].remove(callback)

        return unwatch

    def watch_all(
        self, callback: Callable[[str, Any, Any], None]
    ) -> Callable[[], None]:
        """监听所有状态变化

        Args:
            callback: 回调函数 (key, new_value, old_value) -> None

        Returns:
            取消监听的函数
        """
        self._global_watchers.append(callback)

        def unwatch():
            if callback in self._global_watchers:
                self._global_watchers.remove(callback)

        return unwatch

    def batch(self) -> "BatchContext":
        """开始批量更新（合并通知）

        使用示例：
            with store.batch():
                store.set("a", 1)
                store.set("b", 2)
                store.set("c", 3)
            # 退出 with 时统一通知

        Returns:
            批量上下文管理器
        """
        return BatchContext(self)

    def reset(self, key: Optional[str] = None) -> None:
        """重置状态到默认值

        Args:
            key: 要重置的键，None 表示重置全部
        """
        if key is not None:
            if key in self._defaults:
                self.set(key, self._defaults[key])
        else:
            for k, v in self._defaults.items():
                self.set(k, v)

    def keys(self) -> List[str]:
        """获取所有状态键"""
        return list(self._state.keys())

    def values(self) -> Dict[str, Any]:
        """获取所有状态值（副本）"""
        return dict(self._state)

    def __getitem__(self, key: str) -> Any:
        """支持 store["key"] 语法"""
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """支持 store["key"] = value 语法"""
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        """支持 "key" in store 语法"""
        return key in self._state


class BatchContext:
    """批量更新上下文管理器"""

    def __init__(self, store: Store):
        self._store = store

    def __enter__(self):
        self._store._batch_mode = True
        self._store._batch_changes.clear()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._store._batch_mode = False

        # 统一通知所有变化
        for key, (new_value, old_value) in self._store._batch_changes.items():
            self._store._notify(key, new_value, old_value)

        self._store._batch_changes.clear()
        return False
