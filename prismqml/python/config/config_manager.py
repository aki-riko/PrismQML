# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""
配置管理器 Config Manager - 提供QML友好接口 Provides QML-friendly interface
"""

from collections import deque

from PySide6.QtCore import (
    QCoreApplication,
    QEventLoop,
    QObject,
    Property,
    QTimer,
    Signal,
    Slot,
)

from .app_config import AppConfig, DEFAULT_APP_CONFIG
from ._app_config_schema import resolve_app_config_path
from ..core import debug, error, warning


class ConfigManager(QObject):
    """配置管理器 - 包装AppConfig提供QML友好接口 Config Manager - wraps AppConfig for QML"""
    
    _instance = None
    
    configChanged = Signal()
    lazyLoadingChanged = Signal()
    dwmShadowChanged = Signal()
    dpiScaleChanged = Signal()
    micaEnabledChanged = Signal()
    windowTypeChanged = Signal()
    themeChanged = Signal()
    skinChanged = Signal()
    languageChanged = Signal()
    accentColorChanged = Signal()
    persistencePendingChanged = Signal()
    
    def __new__(cls, config_path: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_path: str = None):
        if self._initialized:
            self._warn_ignored_config_path(config_path)
            return
        super().__init__()
        ready = False
        try:
            self._initialize_config(config_path)
            self._initialized = True
            ready = True
        finally:
            if not ready:
                self._initialized = False
                type(self)._instance = None

    def _warn_ignored_config_path(self, config_path):
        """Warn when a second construction requests another file. 警告路径冲突。"""
        if config_path is None or self._cfg.file is None:
            return
        from pathlib import Path

        requested = Path(config_path)
        if requested != self._cfg.file:
            warning(
                f"ConfigManager 已初始化（路径: {self._cfg.file}），"
                f"忽略新路径: {requested}"
            )

    def _initialize_config(self, config_path):
        """Load, bind, and apply one config instance. 加载、绑定并应用配置。"""
        self._cfg = AppConfig()
        path = resolve_app_config_path(config_path, default=DEFAULT_APP_CONFIG)
        self._cfg.load(path)
        self._pending_updates = deque()
        self._active_persistence = None
        self._connect_config_signals()
        self._apply_appearance_to_runtime()
        app = QCoreApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(lambda: self.waitForPersistence())

    def _connect_config_signals(self):
        """Forward entry changes through the public QML signals. 转发配置信号。"""
        self._cfg.lazy_loading.valueUpdated.connect(self.lazyLoadingChanged)
        self._cfg.dwm_shadow.valueUpdated.connect(self.dwmShadowChanged)
        self._cfg.dpi_scale.valueUpdated.connect(self.dpiScaleChanged)
        self._cfg.mica_enabled.valueUpdated.connect(self.micaEnabledChanged)
        self._cfg.window_type.valueUpdated.connect(self.windowTypeChanged)
        self._cfg.theme.valueUpdated.connect(self.themeChanged)
        self._cfg.skin.valueUpdated.connect(self.skinChanged)
        self._cfg.language.valueUpdated.connect(self.languageChanged)
        self._cfg.accent_color.valueUpdated.connect(self.accentColorChanged)
        self._cfg.configChanged.connect(self.configChanged)
    
    @property
    def cfg(self) -> AppConfig:
        """获取底层AppConfig Get underlying AppConfig"""
        return self._cfg

    def _apply_appearance_to_runtime(self):
        """Apply persisted appearance after loading. 加载后应用持久化外观。"""
        from ..core.theme import getThemeManager

        manager = getThemeManager()
        manager.setThemeFromQml(self.theme)
        manager.setSkinFromQml(self.skin)
        manager.setAccentColor(self.accentColor)

    @Property(bool, notify=persistencePendingChanged)
    def persistencePending(self) -> bool:
        """Whether a serialized background write is active. 是否有后台写入。"""
        return bool(self._active_persistence or self._pending_updates)

    def _set_value(self, entry, value, after_commit=None):
        """Persist on one serial worker before publishing. 串行后台落盘后发布。"""
        if QCoreApplication.instance() is None:
            if self._cfg.set(entry, value) and after_commit is not None:
                after_commit()
            return
        was_pending = self.persistencePending
        self._pending_updates.append((entry, value, after_commit))
        if not was_pending:
            self.persistencePendingChanged.emit()
        self._start_next_persistence()

    def _start_next_persistence(self):
        """Start the next queued snapshot without blocking Qt. 启动下一后台快照。"""
        if self._active_persistence is not None:
            return
        while self._pending_updates:
            entry, value, after_commit = self._pending_updates.popleft()
            update = self._cfg._prepare_update(entry, value)
            if update is None:
                continue
            current, prepared, mapping = update
            from ..core.task_runner import run_in_thread

            try:
                handle = run_in_thread(
                    self._cfg._write_mapping_file, self._cfg.file, mapping
                )
            except Exception as exc:
                error(f"提交配置后台任务失败 Config persistence task failed: {exc}")
                continue
            self._active_persistence = (handle, current, prepared, after_commit)
            handle.succeeded.connect(self._publish_persisted_update)
            handle.finished.connect(self._finish_persistence)
            return
        self.persistencePendingChanged.emit()

    @Slot("QVariant")
    def _publish_persisted_update(self, _result):
        """Commit a successful worker result on the Qt thread. 在 Qt 线程提交。"""
        _handle, current, prepared, after_commit = self._active_persistence
        self._cfg._commit_prepared_update(
            current, prepared, before_notify=after_commit
        )

    @Slot()
    def _finish_persistence(self):
        """Release one worker and continue the serial queue. 释放任务并继续队列。"""
        handle = self._active_persistence[0]
        if handle.failure is not None:
            caught = handle.failure.exception
            error(f"保存失败 Save failed: {caught}")
        self._active_persistence = None
        self._start_next_persistence()

    @Slot("QVariant", result=bool)
    def waitForPersistence(self, timeout_ms=5000) -> bool:
        """Run a nested event loop until queued disk work settles. 等待持久化完成。"""
        if timeout_ms is not None and (
            isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int)
        ):
            raise TypeError("timeout_ms must be an int or None")
        if timeout_ms is not None and timeout_ms < 0:
            raise ValueError("timeout_ms must be non-negative")
        if not self.persistencePending:
            return True
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        self.persistencePendingChanged.connect(loop.quit)
        if timeout_ms is not None:
            timer.start(timeout_ms)
        while self.persistencePending and (timeout_ms is None or timer.isActive()):
            loop.exec()
        self.persistencePendingChanged.disconnect(loop.quit)
        return not self.persistencePending
    
    # ==================== QML Properties ====================
    
    @Property(bool, notify=lazyLoadingChanged)
    def lazyLoading(self) -> bool:
        return self._cfg.get(self._cfg.lazy_loading)

    @Slot(bool)
    def setLazyLoading(self, value: bool):
        self._set_value(self._cfg.lazy_loading, value)

    @Property(bool, notify=dwmShadowChanged)
    def dwmShadow(self) -> bool:
        return self._cfg.get(self._cfg.dwm_shadow)

    @Slot(bool)
    def setDwmShadow(self, value: bool):
        self._set_value(self._cfg.dwm_shadow, value)

    @Property(int, notify=dpiScaleChanged)
    def dpiScale(self) -> int:
        return self._cfg.get(self._cfg.dpi_scale)

    @Property("QVariantList", constant=True)
    def dpiScaleOptions(self):
        return self._cfg.dpi_scale.options

    @Slot("QVariant")
    def setDpiScale(self, value):
        debug(f"setDpiScale: {value}")
        if not self._cfg.dpi_scale.validator.accepts(value):
            warning(f"拒绝无效 dpiScale Invalid dpiScale rejected: {value!r}")
            return
        self._set_value(self._cfg.dpi_scale, value)

    @Property(bool, notify=micaEnabledChanged)
    def micaEnabled(self) -> bool:
        return self._cfg.get(self._cfg.mica_enabled)

    @Slot(bool)
    def setMicaEnabled(self, value: bool):
        debug(f"setMicaEnabled: {value}")
        self._set_value(self._cfg.mica_enabled, value)

    @Property(int, notify=windowTypeChanged)
    def windowType(self) -> int:
        return self._cfg.get(self._cfg.window_type)

    @Property("QVariantList", constant=True)
    def windowTypeOptions(self):
        return self._cfg.window_type.options

    @Slot("QVariant")
    def setWindowType(self, value):
        debug(f"setWindowType: {value}")
        if not self._cfg.window_type.validator.accepts(value):
            warning(f"拒绝无效 windowType Invalid windowType rejected: {value!r}")
            return
        self._set_value(self._cfg.window_type, value)

    @Property(str, notify=themeChanged)
    def theme(self) -> str:
        return self._cfg.get(self._cfg.theme)

    @Property("QVariantList", constant=True)
    def themeOptions(self):
        return self._cfg.theme.options

    @Slot(str)
    def setTheme(self, value: str):
        if not self._cfg.theme.validator.accepts(value):
            warning(f"拒绝无效主题 Invalid theme rejected: {value!r}")
            return
        from ..core.theme import getThemeManager

        self._set_value(
            self._cfg.theme,
            value,
            lambda: getThemeManager().setThemeFromQml(self.theme),
        )

    @Property(str, notify=skinChanged)
    def skin(self) -> str:
        return self._cfg.get(self._cfg.skin)

    @Property("QVariantList", constant=True)
    def skinOptions(self):
        return self._cfg.skin.options

    @Slot(str)
    def setSkin(self, value: str):
        if not self._cfg.skin.validator.accepts(value):
            warning(f"拒绝无效皮肤 Invalid skin rejected: {value!r}")
            return
        from ..core.theme import getThemeManager

        self._set_value(
            self._cfg.skin,
            value,
            lambda: getThemeManager().setSkinFromQml(self.skin),
        )

    @Property(str, notify=languageChanged)
    def language(self) -> str:
        return self._cfg.get(self._cfg.language)

    @Property("QVariantList", constant=True)
    def languageOptions(self):
        return self._cfg.language.options

    @Slot(str)
    def setLanguage(self, value: str):
        if not self._cfg.language.validator.accepts(value):
            warning(f"拒绝无效语言 Invalid language rejected: {value!r}")
            return
        self._set_value(self._cfg.language, value)

    @Property(str, notify=accentColorChanged)
    def accentColor(self) -> str:
        return self._cfg.get(self._cfg.accent_color)

    @Slot(str)
    def setAccentColor(self, value: str):
        from ._app_config_schema import validate_accent_color

        if not validate_accent_color(value):
            warning(f"拒绝无效主题色 Invalid accent color rejected: {value!r}")
            return
        from ..core.theme import getThemeManager

        self._set_value(
            self._cfg.accent_color,
            value,
            lambda: getThemeManager().setAccentColor(self.accentColor),
        )
    
    @Slot(result=str)
    def getConfigPath(self) -> str:
        return str(self._cfg.file) if self._cfg.file else ""


def getConfigManager(config_path: str = None) -> ConfigManager:
    """获取配置管理器单例 Get config manager singleton"""
    return ConfigManager(config_path)
