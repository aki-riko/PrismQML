# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
"""PrismQML State Management - 响应式状态管理

提供现代化的状态管理方案，替代传统的 EventBus：
- Store: 响应式状态存储基类
- 细粒度订阅：只监听关心的 key
- 可追踪：状态变化有迹可循

使用示例：
    from prismqml.state import Store
    
    # 方式1：继承模式（推荐）
    class SettingStore(Store):
        def __init__(self):
            super().__init__()
            self.define("theme", "auto")
            self.define("gpu", False)
    
    settingStore = SettingStore()
    
    # 方式2：直接实例化
    store = Store()
    store.set("key", "value")
    
    # 监听变化
    unwatch = store.watch("theme", lambda new, old: print(f"{old} -> {new}"))
    
    # 取消监听
    unwatch()
"""

from .store import Store

__all__ = ["Store"]
