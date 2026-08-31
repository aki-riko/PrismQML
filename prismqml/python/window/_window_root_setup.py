# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Window root installation and startup finalization. 窗口根对象安装与启动收尾。"""

from ..core.logger import debug
from ._window_startup import _WINDOW_BUILDER_LOG_TAG


def load_window_root(
    builder,
    qml_dir,
    window_qml,
    qml_component,
    window_icon_qml,
    mica_enabled,
    profile,
    startup_profile_verbose,
):
    """Load the stable root, then preserve file and inline fallbacks. 加载稳定根并保留文件与 inline 回退。"""
    loaded_window = builder._load_static_window_boundary(
        qml_dir,
        qml_component,
        window_icon_qml,
        mica_enabled,
        profile,
        startup_profile_verbose,
    )
    if loaded_window is not None:
        return loaded_window

    loaded_window = builder._load_generated_window_boundary(
        window_qml,
        qml_component,
        profile,
        startup_profile_verbose,
    )
    if loaded_window is None:
        builder._engine.loadData(window_qml.encode("utf-8"))
        profile("engine.loadData fallback")
        if builder._engine.rootObjects():
            loaded_window = builder._engine.rootObjects()[-1]
    if loaded_window is None:
        raise RuntimeError("Failed to create window")
    return loaded_window


def install_window_root(builder, loaded_window, profile) -> None:
    """Publish the root before finding content and signals. 先发布根对象再查找内容与信号。"""
    builder._window = loaded_window
    profile("获取 rootObject")
    builder._find_content_area()
    profile("查找 content area")
    builder._connect_signals()
    profile("连接 QML 信号")


def _canonical_window_icon(value) -> str:
    """Normalize only the existing qrc shorthand pair. 仅归一既有 qrc 简写对。"""
    value = str(value)
    if value.startswith("qrc:"):
        return ":/" + value[4:].lstrip("/")
    return value


def _pending_matches_initial(key, pending_value, initial_value) -> bool:
    """Compare a pending value with its rendered initial value. 比较待应用值与渲染初值。"""
    if key == "windowIcon":
        return _canonical_window_icon(pending_value) == _canonical_window_icon(
            initial_value
        )
    return pending_value == initial_value


def _remove_redundant_pending_props(builder, window_icon_qml, mica_enabled) -> None:
    """Drop only values already rendered into the root. 仅移除已渲染到根对象的值。"""
    initial_props = {
        "windowTitle": builder._title,
        "windowIcon": window_icon_qml,
        "windowIconColored": builder._icon_colored,
        "captionActionVisible": bool(
            getattr(builder, "_caption_action_visible", False)
        ),
        "captionActionIcon": getattr(builder, "_caption_action_icon", ""),
        "captionActionToolTip": getattr(
            builder, "_caption_action_tool_tip", ""
        ),
        "captionActionEnabled": bool(
            getattr(builder, "_caption_action_enabled", True)
        ),
        "micaEnabled": mica_enabled,
    }
    for key, initial_value in initial_props.items():
        if key not in builder._pending_props:
            continue
        pending_value = builder._pending_props[key]
        if _pending_matches_initial(key, pending_value, initial_value):
            builder._pending_props.pop(key, None)


def apply_window_pending_state(
    builder, window_icon_qml, mica_enabled, profile
) -> None:
    """Deduplicate, report, and apply pending startup state. 去重、记录并应用启动待处理状态。"""
    _remove_redundant_pending_props(builder, window_icon_qml, mica_enabled)
    if builder._pending_props or builder._pending_calls:
        debug(
            "[启动剖析] PrismQML._create_window pending state: "
            f"props={list(builder._pending_props.keys())}, "
            f"calls={len(builder._pending_calls)}",
            tag=_WINDOW_BUILDER_LOG_TAG,
        )
    builder._apply_pending_state()
    profile("应用 pending state")


def finish_window_startup(
    builder, rendered_window, profile, startup_profile_verbose
) -> None:
    """Install the rendered root and finish startup in order. 按顺序安装渲染根对象并完成启动。"""
    qml_dir, window_qml, qml_component, window_icon_qml, mica_enabled = (
        rendered_window
    )
    loaded_window = load_window_root(
        builder,
        qml_dir,
        window_qml,
        qml_component,
        window_icon_qml,
        mica_enabled,
        profile,
        startup_profile_verbose,
    )
    install_window_root(builder, loaded_window, profile)
    # Apply constructor-time properties before nativeHookReady reads defaults.
    # 在 nativeHookReady 读取默认值前应用构造期属性。
    apply_window_pending_state(builder, window_icon_qml, mica_enabled, profile)
    # NavigationWindowCore owns Splash creation from its initial properties.
    # NavigationWindowCore 根据初始属性统一创建 Splash。
    profile("确认 QML Splash")
