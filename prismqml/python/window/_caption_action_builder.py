# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Title-bar action configuration builder. 标题栏动作配置构建模块。"""

from typing import Any, Callable, Dict


def build_caption_action_template_values(
    builder: Any, escape: Callable[[str], str]
) -> Dict[str, str]:
    """Build escaped Template values for the caption action. 构建转义后的标题栏动作模板值。"""
    visible = bool(getattr(builder, "_caption_action_visible", False))
    enabled = bool(getattr(builder, "_caption_action_enabled", True))
    return {
        "caption_action_visible": "true" if visible else "false",
        "caption_action_icon": escape(getattr(builder, "_caption_action_icon", "")),
        "caption_action_tool_tip": escape(
            getattr(builder, "_caption_action_tool_tip", "")
        ),
        "caption_action_enabled": "true" if enabled else "false",
    }
