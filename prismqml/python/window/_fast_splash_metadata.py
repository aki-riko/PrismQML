# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Fast splash metadata helpers. 快速启动页元数据辅助模块。"""

import sys
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, QImage
from PySide6.QtQuick import QQuickImageProvider

from ..core.logger import warning


DEFAULT_PROCESS_TITLES = {"python", "pythonw", "pyside6"}
ICON_PROVIDER_NAME = "fast-splash-icon"
ICON_PROVIDER_SOURCE = f"image://{ICON_PROVIDER_NAME}/application"
ICON_SIZE = 102


class FastSplashIconProvider(QQuickImageProvider):
    """Expose a legacy QIcon to the isolated splash engine without disk I/O."""

    def __init__(self, icon: Optional[QIcon] = None):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._icon = icon or QIcon()

    def set_icon(self, icon: QIcon) -> None:
        self._icon = icon

    def requestImage(self, image_id: str, size: QSize, requested_size: QSize) -> QImage:
        del image_id
        target_size = requested_size if requested_size.isValid() else QSize(ICON_SIZE, ICON_SIZE)
        image = self._icon.pixmap(target_size).toImage()
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image


def is_default_process_title(title: object) -> bool:
    """Identify Qt's unbranded interpreter title. 识别 Qt 默认解释器标题。"""
    normalized = str(title or "").strip().lower()
    if not normalized:
        return True
    executable_title = Path(sys.executable).stem.strip().lower()
    return normalized in DEFAULT_PROCESS_TITLES or normalized == executable_title


def application_title(app: Optional[Any]) -> str:
    """Read branded display name, then the legacy application name."""
    if app is None:
        return ""
    for getter_name in ("applicationDisplayName", "applicationName"):
        getter = getattr(app, getter_name, None)
        try:
            value = getter() if callable(getter) else getter
        except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
            warning(f"FastSplash 读取应用标题失败: {getter_name}: {exc}")
            continue
        if value and not is_default_process_title(value):
            return str(value)
    return ""


def set_icon_metadata(splash, provider: Optional[FastSplashIconProvider], icon: Any) -> bool:
    """Publish a path/URL or legacy QIcon to an isolated QML surface."""
    if isinstance(icon, QIcon):
        if icon.isNull():
            return False
        if provider is None:
            warning("FastSplash QIcon 来源不可用: 图标 provider 尚未创建")
            return False
        provider.set_icon(icon)
        source = ICON_PROVIDER_SOURCE
    else:
        source = str(icon)
        if not source:
            return False
        source = qml_icon_source(source)
    if splash is not None:
        splash.setProperty("splashIcon", source)
    return True


def qml_icon_source(icon: str) -> str:
    """Normalize a known icon source for an isolated QML engine."""
    source = str(icon).replace("\\", "/")
    if source.startswith(":/"):
        return "qrc" + source
    if source.startswith(("qrc:/", "file:/", "http://", "https://")):
        return source
    if len(source) > 1 and source[1] == ":":
        from PySide6.QtCore import QUrl

        return QUrl.fromLocalFile(source).toString()
    if source.startswith("/"):
        from PySide6.QtCore import QUrl

        return QUrl.fromLocalFile(source).toString()
    return source
