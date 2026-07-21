# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Splash creation helper 启动画面创建辅助模块。"""

import hashlib
import os
import time
from string import Template
from typing import Any

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent

from ..core.logger import debug, exception, warning


_SPLASH_QML_TEMPLATE = Template("""import QtQuick
import "file:///${qml_dir}/controls/feedback/SplashScreen"

SplashScreen {
    iconSource: "${icon_url}"
    title: "${title}"
    subtitle: "${subtitle}"
}
""")


def _profile_generated_splash_qml(
    splash_qml_file,
    profile_values,
) -> None:
    icon_url, title, subtitle = profile_values
    try:
        qml_bytes = splash_qml_file.read_bytes()
        qml_digest = hashlib.sha256(qml_bytes).hexdigest()[:20]
        debug(
            "[启动剖析] PrismQML._create_splash generated qml: "
            f"path={splash_qml_file}, bytes={len(qml_bytes)}, sha={qml_digest}, "
            f"iconSet={bool(icon_url)}, titleSet={bool(title)}, "
            f"subtitleSet={bool(subtitle)}"
        )
    except OSError as exc:
        warning(f"[启动剖析] 读取生成 Splash QML 失败: {exc}")
    debug("[启动剖析] PrismQML._create_splash QQmlComponent(file) begin")


def _log_splash_file_failure(component, exc: Exception) -> None:
    outcome = (
        "文件化加载失败，回退到 inline"
        if component is None
        else "文件化组件已创建，后续诊断失败，保留文件组件"
    )
    exception(f"[Splash] {outcome}: {type(exc).__name__}: {exc}")


def _load_splash_file_component(
    builder: Any,
    splash_qml: str,
    profile,
    verbose: bool,
    profile_values,
):
    component = None
    try:
        splash_qml_file = builder._write_generated_splash_qml(splash_qml)
        profile("写入/确认 Splash QML 缓存")
        if verbose:
            _profile_generated_splash_qml(splash_qml_file, profile_values)
        component = QQmlComponent(
            builder._engine, QUrl.fromLocalFile(str(splash_qml_file))
        )
        profile("QQmlComponent(file)")
        if component.isError():
            warning(
                "[Splash] 文件化组件加载失败: "
                f"{[error.toString() for error in component.errors()]}"
            )
            component = None
    except Exception as exc:
        _log_splash_file_failure(component, exc)
    return component


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


def _render_splash_qml(qml_dir, esc, profile_values) -> str:
    icon_url, title, subtitle = profile_values
    return _SPLASH_QML_TEMPLATE.substitute(
        qml_dir=qml_dir.as_posix(),
        icon_url=esc(icon_url),
        title=esc(title),
        subtitle=esc(subtitle),
    )


def _prepare_splash_qml(builder: Any, profile):
    from ..core.utils import qml_path

    esc = builder._escape_qml
    profile("导入/准备")
    profile_values = _resolve_splash_profile_values(builder)
    splash_qml = _render_splash_qml(qml_path(), esc, profile_values)
    profile("拼接 Splash QML")
    return splash_qml, profile_values


def _splash_profile_verbose() -> bool:
    return os.environ.get("PRISMQML_STARTUP_PROFILE_VERBOSE", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _load_splash_component_with_fallback(
    builder: Any,
    splash_qml: str,
    profile,
    verbose: bool,
    profile_values,
):
    component = _load_splash_file_component(
        builder,
        splash_qml,
        profile,
        verbose,
        profile_values,
    )
    if component is not None:
        return component, "file"

    component = QQmlComponent(builder._engine)
    component.setData(splash_qml.encode("utf-8"), QUrl("inline-splash"))
    profile("component.setData fallback")
    return component, "inline"


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
        splash_qml, profile_values = _prepare_splash_qml(builder, profile)
        component, component_source = _load_splash_component_with_fallback(
            builder,
            splash_qml,
            profile,
            _splash_profile_verbose(),
            profile_values,
        )
        if component.isError():
            warning(f"[Splash] 组件加载失败: {[e.toString() for e in component.errors()]}")
            return

        splash = component.create()
        profile(f"component.create({component_source})")
        if splash is None:
            warning("[Splash] create() 返回 None,跳过启动画面")
            return
        _mount_splash(builder, splash, component, profile)
    except Exception as exc:
        exception(
            "[Splash] 创建启动画面失败(不影响启动): "
            f"{type(exc).__name__}: {exc}"
        )
