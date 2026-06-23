# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是FluentQML的一部分，采用MIT许可证授权。
"""
配置管理器 Config Manager - 提供QML友好接口 Provides QML-friendly interface
"""

from PySide6.QtCore import QObject, Signal, Property, Slot

from .app_config import AppConfig, DEFAULT_APP_CONFIG
from ..core import debug


class ConfigManager(QObject):
    """配置管理器 - 包装AppConfig提供QML友好接口 Config Manager - wraps AppConfig for QML"""
    
    _instance = None
    
    configChanged = Signal()
    lazyLoadingChanged = Signal()
    dwmShadowChanged = Signal()
    dpiScaleChanged = Signal()
    micaEnabledChanged = Signal()
    windowTypeChanged = Signal()
    
    def __new__(cls, config_path: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_path: str = None):
        if self._initialized:
            # 检测 config_path 与已加载路径不一致
            if config_path is not None and self._cfg.file is not None:
                from pathlib import Path
                requested = Path(config_path)
                if requested != self._cfg.file:
                    from ..core import warning
                    warning(
                        f"ConfigManager 已初始化（路径: {self._cfg.file}），"
                        f"忽略新路径: {requested}"
                    )
            return
        super().__init__()
        self._initialized = True
        
        # 创建AppConfig实例 Create AppConfig instance
        self._cfg = AppConfig()
        self._cfg.load(config_path or DEFAULT_APP_CONFIG)
        
        # 连接信号 Connect signals
        AppConfig.lazy_loading.valueUpdated.connect(self.lazyLoadingChanged)
        AppConfig.dwm_shadow.valueUpdated.connect(self.dwmShadowChanged)
        AppConfig.dpi_scale.valueUpdated.connect(self.dpiScaleChanged)
        AppConfig.mica_enabled.valueUpdated.connect(self.micaEnabledChanged)
        AppConfig.window_type.valueUpdated.connect(self.windowTypeChanged)
        self._cfg.configChanged.connect(self.configChanged)
    
    @property
    def cfg(self) -> AppConfig:
        """获取底层AppConfig Get underlying AppConfig"""
        return self._cfg
    
    # ==================== QML Properties ====================
    
    @Property(bool, notify=lazyLoadingChanged)
    def lazyLoading(self) -> bool:
        return self._cfg.get(AppConfig.lazy_loading)

    @Slot(bool)
    def setLazyLoading(self, value: bool):
        self._cfg.set(AppConfig.lazy_loading, value)

    @Property(bool, notify=dwmShadowChanged)
    def dwmShadow(self) -> bool:
        return self._cfg.get(AppConfig.dwm_shadow)

    @Slot(bool)
    def setDwmShadow(self, value: bool):
        self._cfg.set(AppConfig.dwm_shadow, value)

    @Property(int, notify=dpiScaleChanged)
    def dpiScale(self) -> int:
        return self._cfg.get(AppConfig.dpi_scale)

    @Slot(int)
    def setDpiScale(self, value: int):
        debug(f"setDpiScale: {value}")
        self._cfg.set(AppConfig.dpi_scale, value)

    @Property(bool, notify=micaEnabledChanged)
    def micaEnabled(self) -> bool:
        return self._cfg.get(AppConfig.mica_enabled)

    @Slot(bool)
    def setMicaEnabled(self, value: bool):
        debug(f"setMicaEnabled: {value}")
        self._cfg.set(AppConfig.mica_enabled, value)

    @Property(int, notify=windowTypeChanged)
    def windowType(self) -> int:
        return self._cfg.get(AppConfig.window_type)

    @Slot(int)
    def setWindowType(self, value: int):
        debug(f"setWindowType: {value}")
        self._cfg.set(AppConfig.window_type, value)
    
    @Slot(result=str)
    def getConfigPath(self) -> str:
        return str(self._cfg.file) if self._cfg.file else ""


def getConfigManager(config_path: str = None) -> ConfigManager:
    """获取配置管理器单例 Get config manager singleton"""
    return ConfigManager(config_path)
