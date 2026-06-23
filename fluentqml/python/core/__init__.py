# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是FluentQML的一部分，采用MIT许可证授权。
"""FluentQML Core - 核心模块 Core module"""

from .theme import (
    Theme,
    Skin,
    ThemeManager,
    setTheme,
    getTheme,
    setSkin,
    getSkin,
    isDark,
    setAccentColor,
    getAccentColor,
    accentQColor,
    getThemeManager,
)
from .shadow import ShadowManager, getShadowManager, installDwmSyncFilter
from .logger import (
    Logger,
    getLogger,
    debug,
    info,
    warning,
    error,
    exception,
    log_time,
    install_qt_message_handler,
)
from .utils import qml_path, register_types, init_style
from .engine import EngineManager
from .incubation import PrismIncubationController, install_incubation_controller
from .single_instance import SingleInstance, ensure_single_instance
from .updater import Updater
from .icons import Icon
from .icon_base import (
    IconCore,
    resolveIconColor,
    make_icon,
    make_theme_icon,
    paint_icon,
)
from .icon_provider import IconProvider, register_icon_provider, get_icon_provider
from .notification import (
    Position as NotificationPosition,
    Severity as NotificationSeverity,
    showDesktopNotification,
    showDesktopInfo,
    showDesktopSuccess,
    showDesktopWarning,
    showDesktopError,
    showDesktopInfoBar,
    closeAllDesktopNotifications,
)

__all__ = [
    # Theme
    "Theme",
    "Skin",
    "ThemeManager",
    "setTheme",
    "getTheme",
    "setSkin",
    "getSkin",
    "isDark",
    "setAccentColor",
    "getAccentColor",
    "accentQColor",
    "getThemeManager",
    # Shadow
    "ShadowManager",
    "getShadowManager",
    "installDwmSyncFilter",
    # Logger
    "Logger",
    "getLogger",
    "debug",
    "info",
    "warning",
    "error",
    "exception",
    "log_time",
    "install_qt_message_handler",
    # Utils
    "qml_path",
    "register_types",
    "init_style",
    "EngineManager",
    "PrismIncubationController",
    "install_incubation_controller",
    # Single Instance
    "SingleInstance",
    "ensure_single_instance",
    # Updater
    "Updater",
    # Icons
    "Icon",
    "IconCore",
    "resolveIconColor",
    "make_icon",
    "make_theme_icon",
    "paint_icon",
    "IconProvider",
    "register_icon_provider",
    "get_icon_provider",
    # Notification (Python helper, 不需要业务方手撸 NotificationBridge.qml 胶水)
    "NotificationPosition",
    "NotificationSeverity",
    "showDesktopNotification",
    "showDesktopInfo",
    "showDesktopSuccess",
    "showDesktopWarning",
    "showDesktopError",
    "showDesktopInfoBar",
    "closeAllDesktopNotifications",
]
