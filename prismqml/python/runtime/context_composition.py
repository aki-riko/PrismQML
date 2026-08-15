# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""QML context composition owner. QML 上下文装配唯一 owner。"""

from PySide6.QtQml import QQmlApplicationEngine, QQmlContext

from ..core.diagnostics import startup_profile_verbose_enabled
from .context_registry import (
    register_context_properties,
    register_context_property,
    register_image_provider_once,
)


def load_core_window_managers(profile):
    """Load core managers at the window startup boundary. 在窗口启动边界加载核心管理器。"""
    from ..core import ThemeManager, getShadowManager
    from .appearance import install_appearance_persistence
    from .configuration import get_config_manager

    install_appearance_persistence()
    profile("导入核心管理器")
    return ThemeManager, getShadowManager, get_config_manager


def load_window_dependencies(profile):
    """Load window-only dependencies at their original boundary. 在原边界加载窗口依赖。"""
    from .window_services import (
        get_clipboard_helper,
        get_mica_manager,
        get_native_window_hook,
    )

    profile("导入窗口依赖")
    return (
        get_mica_manager,
        get_native_window_hook,
        get_clipboard_helper,
    )


def register_primary_context(context: QQmlContext) -> None:
    """Register shared managers and startup flags. 注册共享管理器与启动开关。"""
    from ..core.incubation import asynchronous_page_loader_enabled
    from ..core.theme import getThemeManager
    from .appearance import install_appearance_persistence
    from .configuration import get_config_manager

    install_appearance_persistence()
    register_context_properties(
        context,
        (
            ("ThemeManager", getThemeManager),
            ("ConfigManager", get_config_manager),
            ("PrismQmlStartupProfileVerbose", startup_profile_verbose_enabled),
            (
                "PrismQmlAsynchronousPageLoaderEnabled",
                asynchronous_page_loader_enabled,
            ),
        ),
    )


def register_lazy_context(
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
    register_context_properties(
        context,
        (
            ("QRCodeGenerator", lambda: qrcode_generator),
            ("ScreenEyedropperManager", lambda: screen_eyedropper_manager),
        ),
    )


def register_window_context(
    engine: QQmlApplicationEngine, context: QQmlContext
) -> None:
    """Register full window services and acrylic provider. 注册完整窗口服务与亚克力源。"""
    from .window_services import (
        get_acrylic_helper,
        get_clipboard_helper,
        get_mica_manager,
        get_native_window_hook,
    )

    register_context_property(context, "MicaManager", get_mica_manager())
    acrylic_helper = get_acrylic_helper()
    register_context_property(context, "AcrylicHelper", acrylic_helper)
    register_context_property(context, "NativeWindow", get_native_window_hook())
    register_context_property(context, "ClipboardHelper", get_clipboard_helper())
    register_image_provider_once(
        engine, "acrylic", lambda: acrylic_helper.imageProvider
    )


def register_support_context(context: QQmlContext) -> None:
    """Register shadow and window helpers. 注册阴影与窗口辅助对象。"""
    from ..core.shadow import getShadowManager
    from .window_services import get_window_helper

    register_context_properties(
        context,
        (("ShadowManager", getShadowManager), ("WindowHelper", get_window_helper)),
    )


def register_window_engine_context(
    builder,
    startup_profile_verbose,
    core_managers,
    window_dependencies,
    profile,
) -> None:
    """Register the reduced window startup contract. 注册精简窗口启动上下文合同。"""
    from ..core.incubation import asynchronous_page_loader_enabled

    ThemeManager, getShadowManager, get_config_manager = core_managers
    get_mica_manager, get_native_window_hook, get_clipboard_helper = (
        window_dependencies
    )
    context = builder._engine.rootContext()
    register_context_properties(
        context,
        (
            ("ThemeManager", ThemeManager),
            ("ShadowManager", getShadowManager),
            ("ConfigManager", get_config_manager),
            ("MicaManager", get_mica_manager),
            ("ClipboardHelper", get_clipboard_helper),
            (
                "PrismQmlStartupProfileVerbose",
                lambda: startup_profile_verbose,
            ),
            (
                "PrismQmlAsynchronousPageLoaderEnabled",
                asynchronous_page_loader_enabled,
            ),
            # WindowCore defers NativeWindow attach/finalizeAttach for DWM animations.
            # WindowCore 延后 NativeWindow attach/finalizeAttach，以保留 DWM 动画。
            ("NativeWindow", get_native_window_hook),
        ),
    )
    profile("注入 ContextProperty")
