# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是PrismQML的一部分，采用MIT许可证授权。

"""PrismQML - A QML-based Fluent Design component library"""

# Allow QML XHR to read local files (needed by Translator to load i18n JSON).
# Must be set before QQmlEngine construction. Downstream code can opt out by setting
# the env var to "0" before importing prismqml.
import os as _os
_os.environ.setdefault("QML_XHR_ALLOW_FILE_READ", "1")

try:
    from importlib.metadata import version as _get_version
    __version__ = _get_version("prismqml")  # PyPI 分发名为 prismqml
except Exception:
    __version__ = "0.2.16"  # 回退值：开发模式或未安装时
__author__ = "aki-riko"

from .python.core import (
    Theme,
    Skin,
    setTheme,
    getTheme,
    setSkin,
    getSkin,
    isDark,
    setAccentColor,
    getAccentColor,
    accentQColor,
    getThemeManager,
    Logger,
    getLogger,
    debug,
    info,
    warning,
    error,
    exception,
    qml_path,
    register_types,
    init_style,
    Icon,
    IconCore,
    resolveIconColor,
    make_icon,
    make_theme_icon,
    paint_icon,
    IconProvider,
    register_icon_provider,
    get_icon_provider,
    ShadowManager,
    getShadowManager,
    installDwmSyncFilter,
    SingleInstance,
    Updater,
)

# 状态管理模块
from .python.state import Store

# 模型模块 (提供长列表高性能数据源)
from .python.models import TableListModel, SqlListModel, DbRouter, is_rust_accelerated

# 窗口模块
from .python.window import (
    App,
    Window,
    WindowCore,
    WindowType,
    NavigationItem,
    MicaManager,
    get_mica_manager,
    AcrylicHelper,
    AcrylicImageProvider,
    get_acrylic_helper,
    # SystemTray
    SystemTrayIcon,
    MessageIcon,
    ActivationReason,
    createSystemTrayIcon,
)

# 功能提供者模块
from .python.providers import (
    QRCodeGenerator,
    QRCodeImageProvider,
    get_qrcode_generator,
    get_qrcode_provider,
    ScreenEyedropperManager,
    get_screen_eyedropper_manager,
    ClipboardHelper,
    get_clipboard_helper,
    SvgImageProvider,
    get_svg_provider,
)

__all__ = [
    # Theme
    "Theme",
    "Skin",
    "setTheme",
    "getTheme",
    "setSkin",
    "getSkin",
    "isDark",
    "setAccentColor",
    "getAccentColor",
    "accentQColor",
    "getThemeManager",
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
    # Shadow
    "ShadowManager",
    "getShadowManager",
    "installDwmSyncFilter",
    # Single Instance
    "SingleInstance",
    "Updater",
    # Window
    "App",
    "Window",
    "WindowCore",
    "WindowType",
    "NavigationItem",
    # Logger
    "Logger",
    "getLogger",
    "debug",
    "info",
    "warning",
    "error",
    "exception",
    # Utils
    "qml_path",
    "register_types",
    "init_style",
    # State
    "Store",
    # QRCode
    "QRCodeGenerator",
    "QRCodeImageProvider",
    "get_qrcode_generator",
    "get_qrcode_provider",
    # Mica & Acrylic
    "MicaManager",
    "get_mica_manager",
    "AcrylicHelper",
    "AcrylicImageProvider",
    "get_acrylic_helper",
    # Screen Eyedropper
    "ScreenEyedropperManager",
    "get_screen_eyedropper_manager",
    # Clipboard
    "ClipboardHelper",
    "get_clipboard_helper",
    # SVG
    "SvgImageProvider",
    "get_svg_provider",
    # SystemTray
    "SystemTrayIcon",
    "MessageIcon",
    "ActivationReason",
    "createSystemTrayIcon",
    # Models
    "TableListModel",
    "SqlListModel",
    "DbRouter",
    "is_rust_accelerated",
]
