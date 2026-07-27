# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Splash configuration builder. 启动画面配置构建模块。"""

from typing import Any, Callable, Dict


def build_splash_properties(builder: Any) -> Dict[str, Any]:
    """Build properties consumed by NavigationWindowCore. 构建窗口基类消费的属性。"""
    icon = getattr(builder, "_splash_icon", "")
    return {
        "splashEnabled": bool(getattr(builder, "_splash_enabled", True)),
        "splashIcon": builder._resolve_icon_path(icon) if icon else "",
        "splashTitle": getattr(builder, "_splash_title", "") or "",
        "splashSubtitle": getattr(builder, "_splash_subtitle", "") or "",
    }


def build_splash_template_values(
    builder: Any, escape: Callable[[str], str]
) -> Dict[str, str]:
    """Build escaped Template values for fallback QML. 构建转义后的回退模板值。"""
    properties = build_splash_properties(builder)
    return {
        "splash_enabled": "true" if properties["splashEnabled"] else "false",
        "splash_icon": escape(properties["splashIcon"]),
        "splash_title": escape(properties["splashTitle"]),
        "splash_subtitle": escape(properties["splashSubtitle"]),
    }
