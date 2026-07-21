# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Splash creation helper 启动画面创建辅助模块。"""

import time
from typing import Any

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent

from ..core.logger import debug, exception, warning


def _splash_component_url():
    from ..core.utils import qml_path

    return QUrl.fromLocalFile(
        str(qml_path() / "controls" / "feedback" / "SplashScreen" / "SplashScreen.qml")
    )


def _make_splash_profile():
    profile_start = time.perf_counter()
    profile_last = profile_start

    def profile(label: str) -> None:
        nonlocal profile_last
        now = time.perf_counter()
        debug(
            f"[启动剖析] PrismQML._create_splash {label}: "
            f"+{int((now - profile_last) * 1000)}ms / "
            f"total {int((now - profile_start) * 1000)}ms"
        )
        profile_last = now

    return profile


def _resolve_splash_profile_values(builder: Any):
    # 图标/标题默认回退到窗口自身配置
    icon = builder._splash_icon or builder._icon
    icon_url = builder._resolve_icon_path(icon) if icon else ""
    title = builder._splash_title or builder._title or ""
    subtitle = builder._splash_subtitle or ""
    return icon_url, title, subtitle


def _prepare_splash_profile(builder: Any, profile):
    profile("导入/准备")
    profile_values = _resolve_splash_profile_values(builder)
    return profile_values


def _load_splash_component(builder: Any, profile):
    component = QQmlComponent(builder._engine, _splash_component_url())
    profile("QQmlComponent(public SplashScreen.qml)")
    if component.isError():
        warning(
            "[Splash] 公共 SplashScreen.qml 加载失败: "
            f"{[error.toString() for error in component.errors()]}"
        )
        return None
    return component


def _create_splash_instance(builder: Any, component, profile_values, profile):
    context = builder._engine.rootContext()
    splash = component.beginCreate(context)
    profile("component.beginCreate(public)")
    if splash is None:
        return None

    icon_url, title, subtitle = profile_values
    splash.setProperty("iconSource", icon_url)
    splash.setProperty("title", title)
    splash.setProperty("subtitle", subtitle)
    component.completeCreate()
    profile("component.completeCreate(public)")
    return splash


def _mount_splash(builder: Any, splash, component, profile) -> None:
    # 挂到窗口 contentItem 作为顶层覆盖层(SplashScreen 内部 anchors.fill)
    splash.setParentItem(builder._window.contentItem())
    splash.setProperty("width", builder._window.width())
    splash.setProperty("height", builder._window.height())
    # QML 端 _dismissSplashWhenReady 读这个引用,首屏就绪时自动 finish()
    builder._window.setProperty("_splashInstance", splash)
    profile("挂载到窗口")
    # 持引用防 GC(QQmlComponent.create 的所有权在调用方)
    builder._splash_instance = splash
    builder._splash_component = component
    debug("[Splash] 启动画面已挂载,等待首屏就绪后自动淡出")


def create_splash(builder: Any) -> None:
    """Create and mount the startup splash 创建并挂载启动画面。"""
    if not builder._splash_enabled or builder._window is None:
        return

    try:
        profile = _make_splash_profile()
        profile_values = _prepare_splash_profile(builder, profile)
        component = _load_splash_component(builder, profile)
        if component is None:
            return

        splash = _create_splash_instance(builder, component, profile_values, profile)
        if splash is None:
            warning("[Splash] beginCreate() 返回 None,跳过启动画面")
            return
        _mount_splash(builder, splash, component, profile)
    except Exception as exc:
        exception(
            "[Splash] 创建启动画面失败(不影响启动): "
            f"{type(exc).__name__}: {exc}"
        )
