# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Real QML QR URL round-trip regressions. 真实 QML 二维码 URL 往返回归。"""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock

import cv2
import numpy as np
from PySide6.QtCore import QCoreApplication, QEventLoop, QSize, QTimer, QUrl
from PySide6.QtGui import QColor, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types
from prismqml.python.providers import qrcode_generator
from prismqml.python.providers._qrcode_protocol import (
    QRCodeRequest,
    decode_provider_id,
    encode_provider_id,
)
from prismqml.python.providers.qrcode_generator import QRCodeImageProvider


QML_LOAD_TIMEOUT_MS = 5000
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

QRCode {
    objectName: "testedQrCode"
}
"""


@dataclass(frozen=True)
class Capture:
    provider_id: str
    requested_size: QSize
    image: QImage


class CapturingQRCodeImageProvider(QRCodeImageProvider):
    """Capture the real ID received from QML before delegating rendering."""

    def __init__(self):
        super().__init__()
        self._captures = []
        self._capture_lock = RLock()

    def requestImage(self, id: str, size, requestedSize):
        image = super().requestImage(id, size, requestedSize)
        capture = Capture(id, QSize(requestedSize), image.copy())
        with self._capture_lock:
            self._captures.append(capture)
        return image

    def capture_for(self, provider_id: str):
        with self._capture_lock:
            return next(
                (
                    capture
                    for capture in reversed(self._captures)
                    if capture.provider_id == provider_id
                ),
                None,
            )


def _wait_until(predicate, timeout_ms: int = QML_LOAD_TIMEOUT_MS) -> bool:
    if predicate():
        return True
    loop = QEventLoop()
    poll = QTimer()
    poll.setInterval(10)
    poll.timeout.connect(lambda: loop.quit() if predicate() else None)
    poll.start()
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()
    poll.stop()
    return predicate()


def _wait_component(component: QQmlComponent) -> None:
    if component.status() == QQmlComponent.Status.Loading:
        loop = QEventLoop()
        component.statusChanged.connect(
            lambda status: loop.quit()
            if status != QQmlComponent.Status.Loading
            else None
        )
        QTimer.singleShot(QML_LOAD_TIMEOUT_MS, loop.quit)
        loop.exec()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]


def _create_component(engine: QQmlApplicationEngine) -> QQmlComponent:
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, QUrl("inline:qrcode-url-protocol.qml"))
    _wait_component(component)
    return component


def _set_initial_properties(component, root, request: QRCodeRequest) -> None:
    component.setInitialProperties(
        root,
        {
            "size": request.size,
            "foregroundColor": QColor(request.foreground),
            "backgroundColor": QColor(request.background),
            "errorLevel": request.error_level,
            "content": request.content,
        },
    )


def _render_real_qml(monkeypatch, request: QRCodeRequest) -> Capture:
    provider = CapturingQRCodeImageProvider()
    monkeypatch.setattr(qrcode_generator, "get_qrcode_provider", lambda: provider)
    engine = QQmlApplicationEngine()
    engine.setParent(QCoreApplication.instance())
    register_types(engine)
    component = _create_component(engine)
    root = component.beginCreate(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _set_initial_properties(component, root, request)
    component.completeCreate()
    expected_provider_id = encode_provider_id(request)
    assert _wait_until(
        lambda: provider.capture_for(expected_provider_id) is not None
        and root.property("imageReady") is True
    )
    capture = provider.capture_for(expected_provider_id)
    root.setParent(engine)
    return capture


def _decoded_text(image: QImage) -> str:
    rgb = image.convertToFormat(QImage.Format.Format_RGB888)
    row_bytes = rgb.bytesPerLine()
    buffer = np.frombuffer(rgb.constBits(), dtype=np.uint8, count=rgb.sizeInBytes())
    rows = buffer.reshape((rgb.height(), row_bytes))
    pixels = rows[:, : rgb.width() * 3].reshape((rgb.height(), rgb.width(), 3)).copy()
    decoded, points, _ = cv2.QRCodeDetector().detectAndDecode(pixels)
    assert points is not None
    return decoded


def test_real_qml_preserves_the_original_failure_vector(qapp, monkeypatch):
    """Verify the exact real input that failed before P7G. 验证修复前真实失败输入。"""
    expected = QRCodeRequest("HELLO", 120, "#112233", "#445566", "H")
    capture = _render_real_qml(monkeypatch, expected)

    assert capture.provider_id == (
        "v1.WzEsIkhFTExPIiwxMjAsIiMxMTIyMzMiLCIjNDQ1NTY2IiwiSCJd"
    )
    assert decode_provider_id(capture.provider_id) == expected
    assert capture.requested_size == QSize(120, 120)
    assert capture.image.size() == QSize(120, 120)
    colors = {
        capture.image.pixelColor(column, row).name().lower()
        for row in range(capture.image.height())
        for column in range(capture.image.width())
    }
    assert expected.foreground in colors
    assert expected.background in colors


def test_real_qml_qrcode_decodes_reserved_unicode_content(qapp, monkeypatch):
    """Decode the image produced by the complete QML/provider chain."""
    content = '你好，PrismQML 😀 |#%?/&=+"\\\n第二行'
    expected = QRCodeRequest(content, 384, "#000000", "#ffffff", "H")
    capture = _render_real_qml(monkeypatch, expected)

    assert decode_provider_id(capture.provider_id) == expected
    assert capture.image.size() == QSize(384, 384)
    assert _decoded_text(capture.image) == content
