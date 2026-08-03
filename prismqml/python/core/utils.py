# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""PrismQML 工具函数"""
import os
from pathlib import Path
from typing import Optional

from PySide6.QtQml import QQmlApplicationEngine, QQmlContext

from .diagnostics import startup_profile_verbose_enabled


QML_XHR_ALLOW_FILE_READ_ENV = "QML_XHR_ALLOW_FILE_READ"
GRAPHICS_API_ENV = "PRISMQML_GRAPHICS_API"
_SUPPORTED_GRAPHICS_APIS = ("direct3d11", "opengl")


def _enable_quick_window_alpha_buffer() -> None:
    """Enable translucent child windows before their native surfaces exist.

    在原生表面创建前启用透明子窗口所需的 alpha buffer。
    """
    from PySide6.QtQuick import QQuickWindow

    QQuickWindow.setDefaultAlphaBuffer(True)


def configure_qml_environment(allow_file_read: bool = True) -> None:
    """Configure process-wide QML rendering before engine creation.

    在引擎创建前配置进程级 QML 渲染环境。

    普通 ``import prismqml`` 不修改该进程环境。使用裸 ``QQmlEngine`` 且需要
    Translator 加载本地 i18n JSON 时，必须在创建引擎前显式调用本函数。
    """
    os.environ[QML_XHR_ALLOW_FILE_READ_ENV] = "1" if allow_file_read else "0"
    _enable_quick_window_alpha_buffer()


def configure_graphics_api(default_api: Optional[str] = None) -> Optional[str]:
    """Select the Qt Quick graphics API before creating a QQuickWindow.

    在创建 QQuickWindow 前选择 Qt Quick 图形后端。环境变量优先于调用方默认值；
    两者均未提供时保持 Qt 自身默认值不变。
    """
    requested_api = os.environ.get(GRAPHICS_API_ENV, default_api)
    if requested_api is None:
        return None
    if not isinstance(requested_api, str):
        raise TypeError("default_api must be a string or None")

    normalized_api = requested_api.strip().lower()
    if not normalized_api:
        return None
    if normalized_api not in _SUPPORTED_GRAPHICS_APIS:
        supported = ", ".join(_SUPPORTED_GRAPHICS_APIS)
        raise ValueError(
            f"{GRAPHICS_API_ENV} must be one of: {supported}; "
            f"got {requested_api!r}"
        )

    from PySide6.QtQuick import QQuickWindow, QSGRendererInterface

    graphics_api = {
        "direct3d11": QSGRendererInterface.GraphicsApi.Direct3D11,
        "opengl": QSGRendererInterface.GraphicsApi.OpenGL,
    }[normalized_api]
    QQuickWindow.setGraphicsApi(graphics_api)
    return normalized_api


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
    from .incubation import asynchronous_page_loader_enabled
    from .theme import getThemeManager
    from ..config import getConfigManager

    context.setContextProperty("ThemeManager", getThemeManager())
    context.setContextProperty("ConfigManager", getConfigManager())
    context.setContextProperty(
        "PrismQmlStartupProfileVerbose", startup_profile_verbose_enabled()
    )
    context.setContextProperty(
        "PrismQmlAsynchronousPageLoaderEnabled",
        asynchronous_page_loader_enabled(),
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
    _enable_quick_window_alpha_buffer()
    context = engine.rootContext()
    _register_primary_context(context)
    _register_lazy_context(engine, context)
    _register_window_context(engine, context)
    _register_support_context(context)
    engine.addImportPath(str(qml_path().parent))
