# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Window engine and QML dependency setup. 窗口引擎与 QML 依赖装配。"""

from ..core.incubation import asynchronous_page_loader_enabled
from ..providers import get_svg_provider
from .context_registry import (
    FULL_CONTEXT_REGISTRATION,
    WINDOW_CONTEXT_REGISTRATION,
    context_registration_level,
    mark_context_registration,
    register_context_property,
    register_image_provider_once,
)
from .engine import get_or_create_qml_engine


def _load_core_window_managers(profile):
    """Load core managers at the original startup boundary. 在原启动边界加载核心管理器。"""
    from ..core import ThemeManager, getShadowManager
    from .appearance import install_appearance_persistence
    from .configuration import get_config_manager

    install_appearance_persistence()
    profile("导入核心管理器")
    return ThemeManager, getShadowManager, get_config_manager


def _ensure_window_engine(builder, profile) -> None:
    """Reuse or create the process QML engine. 复用或创建进程级 QML 引擎。"""
    builder._engine = get_or_create_qml_engine()
    profile("获取/创建 QML Engine")


def _load_window_dependencies(profile):
    """Load window-only dependencies at their original boundary. 在原边界加载窗口依赖。"""
    from ..window.mica_window import get_mica_manager
    from ..window.native_window import get_native_window_hook
    from ..providers.clipboard import get_clipboard_helper

    profile("导入窗口依赖")
    return (
        get_mica_manager,
        get_native_window_hook,
        get_clipboard_helper,
    )


def _inject_window_context(
    builder, startup_profile_verbose, core_managers, window_dependencies, profile
):
    """Inject the ordered root context contract. 按既定顺序注入根上下文合同。"""
    ThemeManager, getShadowManager, get_config_manager = core_managers
    get_mica_manager, get_native_window_hook, get_clipboard_helper = window_dependencies
    context = builder._engine.rootContext()
    register_context_property(context, "ThemeManager", ThemeManager())
    register_context_property(context, "ShadowManager", getShadowManager())
    register_context_property(context, "ConfigManager", get_config_manager())
    register_context_property(context, "MicaManager", get_mica_manager())
    register_context_property(context, "ClipboardHelper", get_clipboard_helper())
    register_context_property(
        context,
        "PrismQmlStartupProfileVerbose", startup_profile_verbose
    )
    register_context_property(
        context,
        "PrismQmlAsynchronousPageLoaderEnabled",
        asynchronous_page_loader_enabled(),
    )
    # WindowCore defers NativeWindow attach/finalizeAttach for DWM animations.
    # WindowCore 延后 NativeWindow attach/finalizeAttach，以保留 DWM 动画。
    register_context_property(context, "NativeWindow", get_native_window_hook())
    profile("注入 ContextProperty")


def _register_window_image_providers(builder, profile) -> None:
    """Register the engine-owned SVG provider. 注册引擎持有的 SVG provider。"""
    registered = register_image_provider_once(
        builder._engine, "svg", get_svg_provider
    )
    profile("注册 ImageProvider" if registered else "复用 ImageProvider")


def prepare_window_engine(builder, startup_profile_verbose, profile):
    """Prepare the engine, context, and providers in startup order. 按启动顺序装配引擎、上下文和 provider。"""
    core_managers = _load_core_window_managers(profile)
    _ensure_window_engine(builder, profile)
    registration_level = context_registration_level(builder._engine)
    if registration_level < FULL_CONTEXT_REGISTRATION:
        if registration_level < WINDOW_CONTEXT_REGISTRATION:
            window_dependencies = _load_window_dependencies(profile)
            _inject_window_context(
                builder,
                startup_profile_verbose,
                core_managers,
                window_dependencies,
                profile,
            )
            mark_context_registration(
                builder._engine, WINDOW_CONTEXT_REGISTRATION
            )
        else:
            profile("复用 ContextProperty")
    else:
        profile("复用完整 ContextProperty")
    _register_window_image_providers(builder, profile)
    return core_managers[2]
