# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""QRCode Generator - 二维码生成器"""

from collections import OrderedDict
from threading import RLock
from typing import Optional

from PySide6.QtCore import QObject, Property, QRect, QSize, Qt, Signal, Slot
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtQuick import QQuickImageProvider

from ..core import exception, warning
from ._qrcode_protocol import (
    DEFAULT_SIZE,
    MAX_CACHE_BYTES as QR_MAX_CACHE_BYTES,
    MAX_CACHE_ENTRIES as QR_MAX_CACHE_ENTRIES,
    MAX_SIZE,
    MIN_SIZE,
    QUIET_ZONE_MODULES,
    QRCodeProtocolError,
    QRCodeRequest,
    build_image_source,
    decode_provider_id,
)

try:
    import qrcode
    from qrcode.constants import (
        ERROR_CORRECT_H,
        ERROR_CORRECT_L,
        ERROR_CORRECT_M,
        ERROR_CORRECT_Q,
    )
    from qrcode.exceptions import DataOverflowError

    HAS_QRCODE = True
except ImportError:
    qrcode = None
    DataOverflowError = OverflowError
    HAS_QRCODE = False


_ERROR_CORRECTION = {
    "L": ERROR_CORRECT_L if HAS_QRCODE else 0,
    "M": ERROR_CORRECT_M if HAS_QRCODE else 0,
    "Q": ERROR_CORRECT_Q if HAS_QRCODE else 0,
    "H": ERROR_CORRECT_H if HAS_QRCODE else 0,
}


class QRCodeImageProvider(QQuickImageProvider):
    """QML图片提供器 - 生成二维码图片"""

    MAX_CACHE_SIZE = QR_MAX_CACHE_ENTRIES
    MAX_CACHE_BYTES = QR_MAX_CACHE_BYTES

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._cache: OrderedDict[str, QImage] = OrderedDict()
        self._cache_bytes = 0
        self._cache_lock = RLock()

    def requestImage(self, id: str, size, requestedSize):
        """Render one canonical provider request without leaking exceptions."""
        if not HAS_QRCODE:
            return self._finalize_image(self._create_placeholder(requestedSize), size)

        try:
            request = decode_provider_id(id)
        except QRCodeProtocolError:
            return self._finalize_image(self._create_placeholder(requestedSize), size)

        cached = self._get_cached(id)
        if cached is not None:
            return self._finalize_image(cached, size)

        image = self._safe_generate(request)
        if image.isNull():
            image = self._create_placeholder(requestedSize)
        else:
            image = self._store_cached(id, image)
        return self._finalize_image(image, size)

    def _safe_generate(self, request: QRCodeRequest) -> QImage:
        try:
            return self._generate_qrcode(request)
        except DataOverflowError:
            warning(
                "二维码内容超出编码容量 "
                f"QR content exceeds encoder capacity: level={request.error_level}"
            )
        except (RuntimeError, ValueError) as exc:
            warning(f"二维码生成失败 QR generation failed: {type(exc).__name__}: {exc}")
        except Exception as exc:
            exception(
                "二维码生成出现未知错误 Unexpected QR generation error: "
                f"{type(exc).__name__}: {exc}"
            )
        return QImage()

    def _generate_qrcode(self, request: QRCodeRequest) -> QImage:
        """Generate an integer-aligned QR image. 生成整数像素对齐二维码。"""
        qr = qrcode.QRCode(
            version=None,
            error_correction=_ERROR_CORRECTION[request.error_level],
            box_size=1,
            border=QUIET_ZONE_MODULES,
        )
        # Match Nayuki C++ makeSegments(): choose one mode for the complete text.
        # 与 C++ Nayuki 保持一致：整串只选择一种编码模式，不自动拆段。
        qr.add_data(request.content, optimize=0)
        qr.make(fit=True)
        return self._render_matrix(qr.get_matrix(), request)

    @classmethod
    def _render_matrix(cls, matrix, request: QRCodeRequest) -> QImage:
        modules = len(matrix)
        module_size = request.size // modules
        if module_size < 1:
            return QImage()

        drawn_size = modules * module_size
        offset = (request.size - drawn_size) // 2
        foreground = QColor(request.foreground)
        image = QImage(request.size, request.size, QImage.Format.Format_RGB32)
        image.fill(QColor(request.background))
        if image.isNull():
            return image

        painter = QPainter(image)
        try:
            cls._paint_modules(
                painter,
                matrix,
                module_size,
                offset,
                foreground,
            )
        finally:
            painter.end()
        return image

    @staticmethod
    def _paint_modules(painter, matrix, module_size, offset, foreground) -> None:
        for row, values in enumerate(matrix):
            for column, enabled in enumerate(values):
                if enabled:
                    painter.fillRect(
                        QRect(
                            offset + column * module_size,
                            offset + row * module_size,
                            module_size,
                            module_size,
                        ),
                        foreground,
                    )

    def _get_cached(self, key: str) -> Optional[QImage]:
        with self._cache_lock:
            image = self._cache.pop(key, None)
            if image is None:
                return None
            self._cache[key] = image
            return image

    def _store_cached(self, key: str, image: QImage) -> QImage:
        cost = int(image.sizeInBytes())
        if cost <= 0 or cost > self.MAX_CACHE_BYTES:
            return image
        with self._cache_lock:
            existing = self._cache.pop(key, None)
            if existing is not None:
                self._cache[key] = existing
                return existing
            while self._cache and (
                len(self._cache) + 1 > self.MAX_CACHE_SIZE
                or self._cache_bytes + cost > self.MAX_CACHE_BYTES
            ):
                _, evicted = self._cache.popitem(last=False)
                self._cache_bytes -= int(evicted.sizeInBytes())
            self._cache[key] = image
            self._cache_bytes += cost
            return image

    @staticmethod
    def _placeholder_size(requested_size: QSize) -> int:
        if (
            isinstance(requested_size, QSize)
            and requested_size.width() == requested_size.height()
            and MIN_SIZE <= requested_size.width() <= MAX_SIZE
        ):
            return requested_size.width()
        return DEFAULT_SIZE

    @classmethod
    def _create_placeholder(cls, requested_size: QSize) -> QImage:
        placeholder_size = cls._placeholder_size(requested_size)
        image = QImage(
            placeholder_size,
            placeholder_size,
            QImage.Format.Format_ARGB32_Premultiplied,
        )
        image.fill(Qt.GlobalColor.transparent)
        return image

    @staticmethod
    def _finalize_image(image: QImage, output_size) -> QImage:
        if isinstance(output_size, QSize):
            output_size.setWidth(image.width())
            output_size.setHeight(image.height())
        return image

    def clear_cache(self):
        """清除缓存"""
        with self._cache_lock:
            self._cache.clear()
            self._cache_bytes = 0


class QRCodeGenerator(QObject):
    """二维码生成器 - 暴露给QML的接口"""

    availableChanged = Signal()

    @Property(bool, notify=availableChanged)
    def available(self) -> bool:
        """检查qrcode库是否可用"""
        return HAS_QRCODE

    @Slot(str, int, str, str, str, result=str)
    def getImageSource(
        self,
        content: str,
        size: int = DEFAULT_SIZE,
        fgColor: str = "#000000",
        bgColor: str = "#ffffff",
        errorLevel: str = "M",
    ) -> str:
        """Return one canonical versioned image URL. 返回规范版本化图片 URL。"""
        if not HAS_QRCODE:
            return ""
        return build_image_source(content, size, fgColor, bgColor, errorLevel)


# 全局实例
_qrcode_generator: Optional[QRCodeGenerator] = None


def get_qrcode_generator() -> QRCodeGenerator:
    """获取二维码生成器单例"""
    global _qrcode_generator
    if _qrcode_generator is None:
        _qrcode_generator = QRCodeGenerator()
    return _qrcode_generator


def get_qrcode_provider() -> QRCodeImageProvider:
    """创建由 QML 引擎持有的二维码图片提供器"""
    return QRCodeImageProvider()
