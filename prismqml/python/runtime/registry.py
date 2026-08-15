# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""QML runtime registry composition. QML 运行时注册装配。"""

from PySide6.QtQml import QQmlApplicationEngine, QQmlContext

from ..core.diagnostics import startup_profile_verbose_enabled
from ..core.utils import _enable_quick_window_alpha_buffer, qml_path


def _register_primary_context(context: QQmlContext) -> None:
    """Register shared managers. 注册共享管理器。"""
    from ..config import getConfigManager
    from ..core.incubation import asynchronous_page_loader_enabled
    from ..core.theme import getThemeManager

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
    from ..core.shadow import getShadowManager
    from ..core.window_helper import get_window_helper

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
