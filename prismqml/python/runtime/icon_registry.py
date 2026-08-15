# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Icon QML context composition. 图标 QML context 装配。"""

from PySide6.QtQml import QQmlEngine

from ..core.icon_provider import get_icon_provider


def register_icon_provider(engine: QQmlEngine) -> None:
    """Inject the explicit Icon context property. 注入显式 Icon context 属性。"""
    engine.rootContext().setContextProperty("Icon", get_icon_provider())
