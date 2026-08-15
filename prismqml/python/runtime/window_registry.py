# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Window engine and QML dependency setup. 窗口引擎与 QML 依赖装配。"""

from .provider_services import get_svg_provider
from .context_registry import (
    FULL_CONTEXT_REGISTRATION,
    WINDOW_CONTEXT_REGISTRATION,
    context_registration_level,
    mark_context_registration,
    register_image_provider_once,
)
from . import context_composition
from .engine import get_or_create_qml_engine


def _ensure_window_engine(builder, profile) -> None:
    """Reuse or create the process QML engine. 复用或创建进程级 QML 引擎。"""
    builder._engine = get_or_create_qml_engine()
    profile("获取/创建 QML Engine")


def _register_window_image_providers(builder, profile) -> None:
    """Register the engine-owned SVG provider. 注册引擎持有的 SVG provider。"""
    registered = register_image_provider_once(
        builder._engine, "svg", get_svg_provider
    )
    profile("注册 ImageProvider" if registered else "复用 ImageProvider")


def prepare_window_engine(builder, startup_profile_verbose, profile):
    """Prepare the engine, context, and providers in startup order. 按启动顺序装配引擎、上下文和 provider。"""
    core_managers = context_composition.load_core_window_managers(profile)
    _ensure_window_engine(builder, profile)
    registration_level = context_registration_level(builder._engine)
    if registration_level < FULL_CONTEXT_REGISTRATION:
        if registration_level < WINDOW_CONTEXT_REGISTRATION:
            window_dependencies = context_composition.load_window_dependencies(
                profile
            )
            context_composition.register_window_engine_context(
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
