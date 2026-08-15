# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""QML runtime registry composition. QML 运行时注册装配。"""

from PySide6.QtQml import QQmlApplicationEngine, QQmlContext

from ..core.diagnostics import startup_profile_verbose_enabled
from ..core.utils import _enable_quick_window_alpha_buffer, qml_path
from .context_registry import (
    FULL_CONTEXT_REGISTRATION,
    mark_context_registration,
    register_context_property,
    register_image_provider_once,
)


def _register_primary_context(context: QQmlContext) -> None:
    """Register shared managers. 注册共享管理器。"""
    from ..core.incubation import asynchronous_page_loader_enabled
    from ..core.theme import getThemeManager
    from .appearance import install_appearance_persistence
    from .configuration import get_config_manager

    install_appearance_persistence()
    register_context_property(context, "ThemeManager", getThemeManager())
    register_context_property(context, "ConfigManager", get_config_manager())
    register_context_property(
        context,
        "PrismQmlStartupProfileVerbose", startup_profile_verbose_enabled()
    )
    register_context_property(
        context,
        "PrismQmlAsynchronousPageLoaderEnabled",
        asynchronous_page_loader_enabled(),
    )


def _register_lazy_context(
    engine: QQmlApplicationEngine, context: QQmlContext
) -> None:
    """Keep lazy proxies alive on their engine. 在引擎上保活延迟代理。"""
    from .lazy_context import (
        LazyQRCodeGenerator,
        LazyScreenEyedropperManager,
    )

    lazy_context_objects = list(
        getattr(engine, "_prismqml_lazy_context_objects", ())
    )
    if len(lazy_context_objects) == 2 and all(
        isinstance(lazy_context_objects[index], expected_type)
        for index, expected_type in enumerate(
            (LazyQRCodeGenerator, LazyScreenEyedropperManager)
        )
    ):
        qrcode_generator, screen_eyedropper_manager = lazy_context_objects
    else:
        qrcode_generator = LazyQRCodeGenerator(engine)
        screen_eyedropper_manager = LazyScreenEyedropperManager()
        lazy_context_objects = [qrcode_generator, screen_eyedropper_manager]
    setattr(engine, "_prismqml_lazy_context_objects", lazy_context_objects)
    register_context_property(context, "QRCodeGenerator", qrcode_generator)
    register_context_property(
        context, "ScreenEyedropperManager", screen_eyedropper_manager
    )


def _register_window_context(
    engine: QQmlApplicationEngine, context: QQmlContext
) -> None:
    """Register window integrations and acrylic provider. 注册窗口集成与亚克力源。"""
    from ..providers.clipboard import get_clipboard_helper
    from ..window import get_acrylic_helper, get_mica_manager, get_native_window_hook

    register_context_property(context, "MicaManager", get_mica_manager())
    acrylic_helper = get_acrylic_helper()
    register_context_property(context, "AcrylicHelper", acrylic_helper)
    register_context_property(context, "NativeWindow", get_native_window_hook())
    register_context_property(context, "ClipboardHelper", get_clipboard_helper())
    register_image_provider_once(
        engine, "acrylic", lambda: acrylic_helper.imageProvider
    )


def _register_support_context(context: QQmlContext) -> None:
    """Register shadow and window helpers. 注册阴影与窗口辅助对象。"""
    from ..core.shadow import getShadowManager
    from ..core.window_helper import get_window_helper

    register_context_property(context, "ShadowManager", getShadowManager())
    register_context_property(context, "WindowHelper", get_window_helper())


def register_types(engine: QQmlApplicationEngine) -> None:
    """Register public QML context and providers. 注册公开 QML 上下文与 provider。"""
    _enable_quick_window_alpha_buffer()
    context = engine.rootContext()
    _register_primary_context(context)
    _register_lazy_context(engine, context)
    _register_window_context(engine, context)
    _register_support_context(context)
    engine.addImportPath(str(qml_path().parent))
    mark_context_registration(engine, FULL_CONTEXT_REGISTRATION)
