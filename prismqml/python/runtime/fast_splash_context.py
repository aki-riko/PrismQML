# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Context setup for the isolated fast splash engine. 独立快速启动引擎上下文装配。"""

from PySide6.QtQml import QQmlEngine

from .appearance import getThemeManager
from .configuration import get_config_manager
from .context_registry import register_context_properties


def register_fast_splash_context(engine: QQmlEngine) -> None:
    """Register only the context required by the reveal transition."""
    register_context_properties(
        engine.rootContext(),
        (
            ("ThemeManager", getThemeManager),
            ("ConfigManager", get_config_manager),
            ("PrismQmlStartupProfileVerbose", lambda: False),
        ),
    )
