# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是PrismQML的一部分，采用MIT许可证授权。

"""IconProvider - 将Icon枚举注入到QML

Usage:
    # 在引擎初始化时
    from prismqml.python.core.icon_provider import register_icon_provider
    register_icon_provider(engine)
    
    # QML中使用
    Icon.get("CALENDAR")  // 返回 "Calendar"
    Icon.getAll()         // 返回所有图标值列表
    Icon.count()          // 返回图标总数 2479
"""

from typing import List
from PySide6.QtCore import QObject, Property, Slot
from PySide6.QtQml import QQmlEngine

from .icons import Icon


class IconProvider(QObject):
    """Icon QML Provider
    
    将Python的Icon枚举暴露给QML使用。
    QML中通过方法访问：Icon.get("CALENDAR")
    
    支持注册自定义图标路径：
        register_custom_icons({"Logo": "qrc:/app/images/icons/Logo.svg"})
    """
    
    _instance = None
    
    def __new__(cls, parent=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, parent=None):
        if self._initialized:
            return
        super().__init__(parent)
        self._initialized = True
        self._icon_dict = {icon.name: icon.value for icon in Icon}
        # 小写下划线格式映射（兼容QML原有用法）
        self._snake_dict = {self._to_snake(icon.name): icon.value for icon in Icon}
        # 自定义图标路径映射 Custom icon path mapping
        self._custom_paths = {}
    
    @staticmethod
    def _to_snake(name: str) -> str:
        """将 UPPER_CASE 转换为 lower_case"""
        return name.lower()
    
    def __getattr__(self, name: str) -> str:
        """支持属性访问：Icon.CALENDAR（Python侧）"""
        if name.startswith('_'):
            return super().__getattribute__(name)
        if name in self._icon_dict:
            return self._icon_dict[name]
        # 尝试小写格式
        if name in self._snake_dict:
            return self._snake_dict[name]
        raise AttributeError(f"Icon has no icon '{name}'")
    
    def register_custom_icon(self, name: str, path: str):
        """注册自定义图标路径
        
        Args:
            name: 图标名称（如 "Logo"）
            path: 图标文件路径（如 "qrc:/app/images/icons/Logo.svg"）
        """
        self._custom_paths[name] = path
    
    def register_custom_icons(self, icons: dict):
        """批量注册自定义图标路径
        
        Args:
            icons: {图标名: 路径} 字典
        """
        self._custom_paths.update(icons)
    
    @Slot(str, result=str)
    def getPath(self, name: str) -> str:
        """获取图标路径（优先返回自定义路径）
        
        Args:
            name: 图标名称
            
        Returns:
            图标路径，自定义图标返回完整路径，Icon返回空字符串
        """
        # 先检查自定义图标
        if name in self._custom_paths:
            return self._custom_paths[name]
        return ""
    
    @Slot(str, result=bool)
    def isCustomIcon(self, name: str) -> bool:
        """检查是否为自定义图标"""
        return name in self._custom_paths
    
    @Slot(str, result=str)
    def get(self, name: str) -> str:
        """通过名称获取图标值
        
        Args:
            name: 枚举名，支持 "CALENDAR" 或 "calendar" 格式
            
        Returns:
            图标值，如 "Calendar"
        """
        # 先尝试原始格式
        if name in self._icon_dict:
            return self._icon_dict[name]
        # 尝试大写格式
        upper_name = name.upper()
        if upper_name in self._icon_dict:
            return self._icon_dict[upper_name]
        # 尝试小写格式
        lower_name = name.lower()
        if lower_name in self._snake_dict:
            return self._snake_dict[lower_name]
        return ""
    
    @Slot(result=list)
    def getAll(self) -> List[str]:
        """获取所有图标值列表"""
        return list(self._icon_dict.values())
    
    @Slot(result=list)
    def getAllNames(self) -> List[str]:
        """获取所有枚举名列表（大写格式）"""
        return list(self._icon_dict.keys())
    
    @Slot(result=int)
    def count(self) -> int:
        """获取图标总数"""
        return len(self._icon_dict)


def get_icon_provider() -> IconProvider:
    """获取全局IconProvider单例"""
    return IconProvider()


def register_icon_provider(engine: QQmlEngine):
    """注册Icon到QML引擎
    
    Args:
        engine: QML引擎实例
    """
    provider = get_icon_provider()
    engine.rootContext().setContextProperty("Icon", provider)
