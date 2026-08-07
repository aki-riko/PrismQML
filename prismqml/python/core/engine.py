# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""
引擎管理器

提供对全局 QQmlApplicationEngine 的访问
"""

from typing import Optional
from PySide6.QtQml import QQmlApplicationEngine


_ENGINE_BINDINGS_ATTR = "_prismqml_engine_bindings"


class EngineManager:
    """QML引擎管理器，管理全局唯一的QQmlApplicationEngine实例"""
    
    _engine: Optional[QQmlApplicationEngine] = None
    
    @classmethod
    def set_engine(cls, engine: QQmlApplicationEngine):
        """设置全局引擎"""
        cls._engine = engine
        
    @classmethod
    def get_engine(cls) -> QQmlApplicationEngine:
        if cls._engine is None:
            raise RuntimeError("Engine not initialized.")
        return cls._engine

    @staticmethod
    def register_engine_binding(engine: QQmlApplicationEngine, binding) -> None:
        """Keep one binding alive until its QML engine resets. 保活绑定直到 QML 引擎重置。"""
        bindings = getattr(engine, _ENGINE_BINDINGS_ATTR, [])
        if not any(current is binding for current in bindings):
            bindings.append(binding)
        setattr(engine, _ENGINE_BINDINGS_ATTR, bindings)

    @staticmethod
    def _release_engine_bindings(engine: QQmlApplicationEngine) -> None:
        """Release Python objects that hold this engine. 释放持有该引擎的绑定对象。"""
        bindings = (
            tuple(getattr(engine, _ENGINE_BINDINGS_ATTR, ()))
            + tuple(getattr(engine, "_prismqml_lazy_context_objects", ()))
        )
        released = set()
        for binding in bindings:
            binding_id = id(binding)
            if binding_id in released:
                continue
            released.add(binding_id)
            release_engine = getattr(binding, "release_engine", None)
            if release_engine is not None:
                release_engine()
        setattr(engine, _ENGINE_BINDINGS_ATTR, [])
        setattr(engine, "_prismqml_lazy_context_objects", [])

    @classmethod
    def reset(cls):
        """重置引擎引用（用于测试和热重载场景）Reset engine reference (for testing and hot-reload)"""
        engine = cls._engine
        cls._engine = None
        if engine is not None:
            cls._release_engine_bindings(engine)
