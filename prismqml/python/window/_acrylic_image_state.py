# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Thread-safe acrylic image cache state. 线程安全的亚克力图像缓存状态。"""

from threading import Lock
from typing import Optional

from PySide6.QtGui import QImage


class _AcrylicImageState:
    """Shared acrylic image data without QML-engine ownership. 亚克力共享图像状态。"""

    def __init__(self):
        self._lock = Lock()
        self._current_image: Optional[QImage] = None
        self._image_id = 0

    def image(self) -> Optional[QImage]:
        """Return a detached image snapshot. 返回图像快照。"""
        with self._lock:
            return QImage(self._current_image) if self._current_image is not None else None

    def set_image(self, image: QImage) -> None:
        """Store an image and advance its cache id. 保存图像并递增缓存标识。"""
        with self._lock:
            self._current_image = QImage(image)
            self._image_id += 1

    @property
    def image_id(self) -> int:
        """Return the current cache id. 返回当前缓存标识。"""
        with self._lock:
            return self._image_id
