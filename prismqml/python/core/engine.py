# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是 FluentQML 的一部分，采用 MIT 许可证授权。
# Copyright 2026 aki-riko

"""
引擎管理器

提供对全局 QQmlApplicationEngine 的访问
"""

from typing import Optional
from PySide6.QtQml import QQmlApplicationEngine

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

    @classmethod
    def reset(cls):
        """重置引擎引用（用于测试和热重载场景）Reset engine reference (for testing and hot-reload)"""
        cls._engine = None
