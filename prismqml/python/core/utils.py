# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""PrismQML 工具函数"""
import os
from pathlib import Path
from PySide6.QtQml import QQmlApplicationEngine, QQmlContext

from .diagnostics import startup_profile_verbose_enabled


QML_XHR_ALLOW_FILE_READ_ENV = "QML_XHR_ALLOW_FILE_READ"


def configure_qml_environment(allow_file_read: bool = True) -> None:
    """Configure local QML XHR before engine creation. 配置 QML 本地文件读取。

    普通 ``import prismqml`` 不修改该进程环境。使用裸 ``QQmlEngine`` 且需要
    Translator 加载本地 i18n JSON 时，必须在创建引擎前显式调用本函数。
    """
    os.environ[QML_XHR_ALLOW_FILE_READ_ENV] = "1" if allow_file_read else "0"


def qml_path(relative_path: str = "") -> Path:
    """获取QML文件路径

    返回的目录即 QML module 根（`module PrismQML` 在其 qmldir 中声明）。
    Qt 6 QML 要求 importPath 指向该目录的**父**（见 register_types 中的 addImportPath）。
    """
    base = Path(__file__).parent.parent.parent / "PrismQML"
    if relative_path:
        return base / relative_path
    return base


def init_style():
    """
    初始化QML控件样式为Basic，禁用原生平台样式
    必须在创建QGuiApplication之前调用
    """
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"


def _register_primary_context(context: QQmlContext) -> None:
    """Register shared managers. 注册共享管理器。"""
    from .theme import getThemeManager
    from ..config import getConfigManager

    context.setContextProperty("ThemeManager", getThemeManager())
    context.setContextProperty("ConfigManager", getConfigManager())
    context.setContextProperty(
        "PrismQmlStartupProfileVerbose", startup_profile_verbose_enabled()
    )


def _register_lazy_context(
    engine: QQmlApplicationEngine, context: QQmlContext
) -> None:
    """Keep lazy proxies alive on their engine. 在引擎上保活延迟代理。"""
    from ..providers.lazy_context import (
        LazyQRCodeGenerator,
        LazyScreenEyedropperManager,
    )

    lazy_context_objects = getattr(engine, "_prismqml_lazy_context_objects", [])
    qrcode_generator = LazyQRCodeGenerator(engine)
    screen_eyedropper_manager = LazyScreenEyedropperManager()
    lazy_context_objects.extend([qrcode_generator, screen_eyedropper_manager])
    setattr(engine, "_prismqml_lazy_context_objects", lazy_context_objects)
    context.setContextProperty("QRCodeGenerator", qrcode_generator)
    context.setContextProperty("ScreenEyedropperManager", screen_eyedropper_manager)


def _register_window_context(
    engine: QQmlApplicationEngine, context: QQmlContext
) -> None:
    """Register window integrations and acrylic provider. 注册窗口集成与亚克力源。"""
    from ..providers.clipboard import get_clipboard_helper
    from ..window import get_acrylic_helper, get_mica_manager, get_native_window_hook

    context.setContextProperty("MicaManager", get_mica_manager())
    acrylic_helper = get_acrylic_helper()
    context.setContextProperty("AcrylicHelper", acrylic_helper)
    context.setContextProperty("NativeWindow", get_native_window_hook())
    context.setContextProperty("ClipboardHelper", get_clipboard_helper())
    engine.addImageProvider("acrylic", acrylic_helper.imageProvider)


def _register_support_context(context: QQmlContext) -> None:
    """Register shadow and window helpers. 注册阴影与窗口辅助对象。"""
    from .shadow import getShadowManager
    from .window_helper import get_window_helper

    context.setContextProperty("ShadowManager", getShadowManager())
    context.setContextProperty("WindowHelper", get_window_helper())


def register_types(engine: QQmlApplicationEngine) -> None:
    """Register public QML context and providers. 注册公开 QML 上下文与 provider。"""
    context = engine.rootContext()
    _register_primary_context(context)
    _register_lazy_context(engine, context)
    _register_window_context(engine, context)
    _register_support_context(context)
    engine.addImportPath(str(qml_path().parent))
