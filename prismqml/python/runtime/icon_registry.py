# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Icon QML context composition. 图标 QML context 装配。"""

from PySide6.QtQml import QQmlEngine

from ..core.icon_provider import IconProvider, get_icon_provider as _get_icon_provider
from .context_registry import register_context_property


def get_icon_provider() -> IconProvider:
    """Return the process IconProvider singleton. 返回进程级 IconProvider 单例。"""
    return _get_icon_provider()


def register_icon_provider(engine: QQmlEngine) -> None:
    """Inject the explicit Icon context property. 注入显式 Icon context 属性。"""
    register_context_property(
        engine.rootContext(), "Icon", get_icon_provider()
    )
