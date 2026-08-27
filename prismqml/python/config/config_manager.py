# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""
配置管理器 Config Manager - 提供QML友好接口 Provides QML-friendly interface
"""

from collections import deque
import json
import os

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
from ._app_config_schema import (
    CONFIG_FILE_PATH_ENVIRONMENT,
    resolve_app_config_path,
)
from ..core import debug, error, exception, warning


def _remove_obsolete_window_fields(file_path, writer):
    """Remove retired Window fields while preserving the rest of the JSON. 删除废弃字段并保留其余配置。"""
    try:
        with open(file_path, encoding="utf-8") as stream:
            payload = json.load(stream)
    except FileNotFoundError:
        return False
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        warning(f"读取旧配置迁移失败 Legacy config migration read failed: {exc}")
        return False

    if not isinstance(payload, dict):
        return False
    window = payload.get("Window")
    if not isinstance(window, dict) or "LazyAnimationType" not in window:
        return False

    del window["LazyAnimationType"]
    try:
        writer(file_path, payload)
    except Exception as exc:
        warning(f"删除旧配置字段失败 Legacy config cleanup failed: {exc}")
        return False
    return True


def _write_window_mapping_preserving_appearance(
    writer, file_path, mapping
):
    """Merge the latest unowned Appearance in the worker. 后台合并最新未托管外观。"""
    try:
        with open(file_path, encoding="utf-8") as stream:
            current = json.load(stream)
    except FileNotFoundError:
        current = {}
    if not isinstance(current, dict):
        raise ValueError("configuration root must be an object")
    appearance = current.get("Appearance")
    if appearance is not None:
        if not isinstance(appearance, dict):
            raise ValueError("Appearance must be an object")
        mapping["Appearance"] = appearance
    writer(file_path, mapping)


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
    
    def __new__(
        cls, config_path: str = None, *, persist_appearance: bool = None
    ):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(
        self, config_path: str = None, *, persist_appearance: bool = None
    ):
        if self._initialized:
            self._validate_existing_request(config_path, persist_appearance)
            return
        super().__init__()
        ready = False
        try:
            self._initialize_config(config_path, persist_appearance)
            self._initialized = True
            ready = True
        finally:
            if not ready:
                self._initialized = False
                type(self)._instance = None

    def _validate_existing_request(self, config_path, persist_appearance):
        """Reject conflicting singleton configuration. 拒绝冲突的单例配置。"""
        if config_path is not None:
            requested = resolve_app_config_path(
                config_path, default=DEFAULT_APP_CONFIG
            )
            if requested != self._cfg.file:
                raise RuntimeError(
                    "ConfigManager requested with a different configuration path: "
                    f"initialized={self._cfg.file}, requested={requested}"
                )
        if (
            persist_appearance is not None
            and self._resolve_appearance_persistence(None, persist_appearance)
            != self._persist_appearance
        ):
            raise RuntimeError(
                "ConfigManager requested with a different appearance persistence policy"
            )

    @staticmethod
    def _resolve_appearance_persistence(config_path, requested):
        if requested is not None:
            if type(requested) is not bool:
                raise TypeError("persist_appearance must be a bool or None")
            return requested
        return bool(config_path) or bool(
            os.environ.get(CONFIG_FILE_PATH_ENVIRONMENT)
        )

    def _initialize_config(self, config_path, persist_appearance):
        """Load, bind, and apply one config instance. 加载、绑定并应用配置。"""
        self._cfg = AppConfig()
        path = resolve_app_config_path(config_path, default=DEFAULT_APP_CONFIG)
        self._persist_appearance = self._resolve_appearance_persistence(
            config_path, persist_appearance
        )
        loaded = self._cfg.load(path)
        if loaded:
            _remove_obsolete_window_fields(path, self._cfg._write_mapping_file)
        if not self._persist_appearance:
            self._reset_loaded_appearance()
        self._pending_updates = deque()
        self._active_persistence = None
        self._runtime_overrides = {}
        self._runtime_request_id = 0
        self._appearance_runtime = None
        self._connect_config_signals()
        app = QCoreApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(lambda: self.waitForPersistence())

    def _reset_loaded_appearance(self):
        """Keep implicit hosts on runtime defaults. 隐式宿主保持运行时默认外观。"""
        for entry in (
            self._cfg.theme,
            self._cfg.skin,
            self._cfg.language,
            self._cfg.accent_color,
        ):
            entry._replace_value(entry.default_value, False)

    def _initialize_ephemeral_appearance(self, theme, skin, accent_color):
        """Mirror explicit pre-registration runtime values. 镜像注册前显式运行时值。"""
        for entry, value in (
            (self._cfg.theme, theme),
            (self._cfg.skin, skin),
            (self._cfg.accent_color, accent_color),
        ):
            prepared = entry.prepare(value)
            entry._replace_value(prepared, False)

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

    @Property(bool, constant=True)
    def appearancePersistenceEnabled(self) -> bool:
        """Whether Appearance is application-owned and persisted. 是否持久化应用外观。"""
        return self._persist_appearance

    def _bind_appearance_runtime(
        self, apply_appearance, *, apply_persisted: bool = True
    ):
        """Bind and initialize the outer appearance port. 绑定并初始化外观端口。"""
        if self._appearance_runtime is apply_appearance:
            return
        previous = self._appearance_runtime
        self._appearance_runtime = apply_appearance
        ready = False
        try:
            if apply_persisted:
                self._apply_appearance_to_runtime()
            ready = True
        finally:
            if not ready:
                self._appearance_runtime = previous

    def _apply_appearance_to_runtime(self):
        """Apply persisted appearance through the bound port. 通过端口应用外观。"""
        if self._appearance_runtime is None:
            return
        self._appearance_runtime("theme", self.theme)
        self._appearance_runtime("skin", self.skin)
        self._appearance_runtime("accent_color", self.accentColor)

    def _set_ephemeral_appearance(self, entry, value, apply_runtime=None):
        """Publish one process-only appearance value. 发布仅进程内生效的外观。"""
        if apply_runtime is not None:
            apply_runtime(value)
        self._cfg.set(entry, value, save=False)

    def _apply_runtime_appearance(self, field, value):
        """Apply one runtime value when the outer port is bound. 应用单项运行时值。"""
        if self._appearance_runtime is not None:
            self._appearance_runtime(field, value)

    @Property(bool, notify=persistencePendingChanged)
    def persistencePending(self) -> bool:
        """Whether a serialized background write is active. 是否有后台写入。"""
        return bool(self._active_persistence or self._pending_updates)

    def _set_value(
        self, entry, value, after_commit=None, after_failure=None
    ):
        """Persist on one serial worker before publishing. 串行后台落盘后发布。"""
        if QCoreApplication.instance() is None:
            if self._set_value_without_application(entry, value):
                if after_commit is not None:
                    after_commit()
            elif after_failure is not None:
                after_failure()
            return
        was_pending = self.persistencePending
        self._pending_updates.append(
            (entry, value, after_commit, after_failure)
        )
        if not was_pending:
            self.persistencePendingChanged.emit()
        self._start_next_persistence()

    def _set_value_without_application(self, entry, value):
        """Persist synchronously before a Qt application exists. Qt 应用创建前同步保存。"""
        if self._persist_appearance:
            return self._cfg.set(entry, value)
        update = self._cfg._prepare_update(entry, value)
        if update is None:
            return True
        current, prepared, mapping = update
        mapping.pop("Appearance", None)
        try:
            _write_window_mapping_preserving_appearance(
                self._cfg._write_mapping_file, self._cfg.file, mapping
            )
        except Exception as exc:
            exception(f"保存失败 Save failed: {exc}")
            return False
        self._cfg._commit_prepared_update(current, prepared)
        return True

    def _set_runtime_value(
        self, entry, value, apply_runtime, apply_committed
    ):
        """Apply a public engine setting now and persist it in the background."""
        apply_runtime(value)
        field = entry.name
        self._runtime_request_id += 1
        request_id = self._runtime_request_id
        self._runtime_overrides[field] = request_id
        committed = lambda: self._settle_runtime_override(
            field, request_id, False, apply_committed
        )
        failed = lambda: self._settle_runtime_override(
            field, request_id, True, apply_committed
        )
        self._set_value(entry, value, committed, failed)

    def _settle_runtime_override(
        self, field, request_id, failed, apply_committed
    ):
        """Release only the matching immediate-runtime request. 释放匹配请求。"""
        if self._runtime_overrides.get(field) != request_id:
            return
        self._runtime_overrides.pop(field, None)
        if failed:
            apply_committed()

    def _start_next_persistence(self):
        """Start the next queued snapshot without blocking Qt. 启动下一后台快照。"""
        if self._active_persistence is not None:
            return
        while self._pending_updates:
            entry, value, after_commit, after_failure = (
                self._pending_updates.popleft()
            )
            update = self._cfg._prepare_update(entry, value)
            if update is None:
                if after_commit is not None:
                    after_commit()
                continue
            if self._launch_persistence(update, after_commit, after_failure):
                return
        self.persistencePendingChanged.emit()

    def _launch_persistence(self, update, after_commit, after_failure):
        """Launch one prepared disk write. 启动一次已准备的磁盘写入。"""
        current, prepared, mapping = update
        writer = self._cfg._write_mapping_file
        arguments = (self._cfg.file, mapping)
        if not self._persist_appearance:
            mapping.pop("Appearance", None)
            arguments = (writer, self._cfg.file, mapping)
            writer = _write_window_mapping_preserving_appearance
        from ..core.task_runner import run_in_thread

        try:
            handle = run_in_thread(writer, *arguments)
        except Exception as exc:
            error(f"提交配置后台任务失败 Config persistence task failed: {exc}")
            if after_failure is not None:
                after_failure()
            return False
        self._active_persistence = (
            handle, current, prepared, after_commit, after_failure
        )
        handle.succeeded.connect(self._publish_persisted_update)
        handle.finished.connect(self._finish_persistence)
        return True

    @Slot("QVariant")
    def _publish_persisted_update(self, _result):
        """Commit a successful worker result on the Qt thread. 在 Qt 线程提交。"""
        _handle, current, prepared, after_commit, _after_failure = (
            self._active_persistence
        )
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
            after_failure = self._active_persistence[4]
            if after_failure is not None:
                after_failure()
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

        if not self._persist_appearance:
            self._set_ephemeral_appearance(
                self._cfg.theme,
                value,
                lambda candidate: self._apply_runtime_appearance(
                    "theme", candidate
                ),
            )
            return

        self._set_runtime_value(
            self._cfg.theme,
            value,
            lambda candidate: self._apply_runtime_appearance("theme", candidate),
            lambda: self._apply_runtime_appearance("theme", self.theme),
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

        if not self._persist_appearance:
            self._set_ephemeral_appearance(
                self._cfg.skin,
                value,
                lambda candidate: self._apply_runtime_appearance(
                    "skin", candidate
                ),
            )
            return

        self._set_runtime_value(
            self._cfg.skin,
            value,
            lambda candidate: self._apply_runtime_appearance("skin", candidate),
            lambda: self._apply_runtime_appearance("skin", self.skin),
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
        if self._persist_appearance:
            self._set_value(self._cfg.language, value)
        else:
            self._set_ephemeral_appearance(self._cfg.language, value)

    @Property(str, notify=accentColorChanged)
    def accentColor(self) -> str:
        return self._cfg.get(self._cfg.accent_color)

    @Slot(str)
    def setAccentColor(self, value: str):
        from ._app_config_schema import validate_accent_color

        if not validate_accent_color(value):
            warning(f"拒绝无效主题色 Invalid accent color rejected: {value!r}")
            return

        if not self._persist_appearance:
            self._set_ephemeral_appearance(
                self._cfg.accent_color,
                value,
                lambda candidate: self._apply_runtime_appearance(
                    "accent_color", candidate
                ),
            )
            return

        self._set_runtime_value(
            self._cfg.accent_color,
            value,
            lambda candidate: self._apply_runtime_appearance(
                "accent_color", candidate
            ),
            lambda: self._apply_runtime_appearance(
                "accent_color", self.accentColor
            ),
        )
    
    @Slot(result=str)
    def getConfigPath(self) -> str:
        return str(self._cfg.file) if self._cfg.file else ""


def getConfigManager(
    config_path: str = None, *, persist_appearance: bool = None
) -> ConfigManager:
    """获取配置管理器单例 Get config manager singleton"""
    return ConfigManager(
        config_path, persist_appearance=persist_appearance
    )
