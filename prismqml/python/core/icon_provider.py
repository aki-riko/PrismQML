# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Explicit Fluent icon path provider. 显式 Fluent 图标路径提供器。

The QML context registration entrypoint is exposed by ``prismqml``. QML context
注册入口由 ``prismqml`` 公开。

    // QML中使用 QML usage
    Icon.getPath("Add")
    Icon.isValid("Add")
"""

from PySide6.QtCore import QObject, Slot
from .utils import qml_path


FLUENT_ICON_DIRECTORY = "controls/icons/fluent"


def _icon_path(name: str):
    return qml_path(FLUENT_ICON_DIRECTORY) / f"{name}.svg"


class IconProvider(QObject):
    """Map Fluent icon values to packaged SVG paths. 映射图标值到 SVG 路径。"""

    _instance = None

    def __new__(cls, parent=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, parent=None):
        if self._initialized:
            return
        super().__init__(parent)
        self._initialized = True

    @Slot(str, result=str)
    def getPath(self, name: str) -> str:
        """Return the packaged SVG path for an icon value. 返回 SVG 路径。"""
        return str(_icon_path(name))

    @Slot(str, result=bool)
    def isValid(self, name: str) -> bool:
        """Return whether the packaged SVG exists. 返回 SVG 是否存在。"""
        return _icon_path(name).is_file()


def get_icon_provider() -> IconProvider:
    """Return the process IconProvider singleton. 返回进程级单例。"""
    return IconProvider()
