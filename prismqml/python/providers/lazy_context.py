# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Lazy QML context providers.

These lightweight proxies keep App/engine creation from importing optional
providers that are only needed by specific controls.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlApplicationEngine


class LazyQRCodeGenerator(QObject):
    """QML-compatible QRCodeGenerator proxy.

    Importing the real QR code backend pulls in the optional qrcode package.
    Most apps never create a QRCode control on their first screen, so defer it
    until QML reads ``available`` or asks for an image source.
    """

    availableChanged = Signal()

    def __init__(self, engine: QQmlApplicationEngine, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._engine: Optional[QQmlApplicationEngine] = engine
        self._generator = None
        self._provider_registered = False

    def _ensure_generator(self):
        if self._generator is None:
            from .qrcode_generator import get_qrcode_generator

            self._generator = get_qrcode_generator()
        return self._generator

    def _ensure_provider(self) -> None:
        if self._provider_registered:
            return
        if self._engine is None:
            raise RuntimeError("QML engine is no longer available")
        from .qrcode_generator import get_qrcode_provider

        self._engine.addImageProvider("qrcode", get_qrcode_provider())
        self._provider_registered = True

    def release_engine(self) -> None:
        """Release the engine wrapper during reset. 重置时释放引擎绑定。"""
        self._engine = None
        self._provider_registered = False

    @Property(bool, notify=availableChanged)
    def available(self) -> bool:
        return bool(self._ensure_generator().available)

    @Slot(str, int, str, str, str, result=str)
    def getImageSource(
        self,
        content: str,
        size: int = 150,
        fgColor: str = "#000000",
        bgColor: str = "#ffffff",
        errorLevel: str = "M",
    ) -> str:
        self._ensure_provider()
        return self._ensure_generator().getImageSource(
            content,
            size,
            fgColor,
            bgColor,
            errorLevel,
        )


class LazyScreenEyedropperManager(QObject):
    """QML-compatible ScreenEyedropperManager proxy."""

    colorPicked = Signal(QColor)
    pickingStarted = Signal()
    pickingFinished = Signal()
    pickingCancelled = Signal()

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._manager = None
        self._connected = False

    def _ensure_manager(self):
        if self._manager is None:
            from .screen_eyedropper import get_screen_eyedropper_manager

            self._manager = get_screen_eyedropper_manager()
        if not self._connected:
            self._manager.colorPicked.connect(self.colorPicked.emit)
            self._manager.pickingStarted.connect(self.pickingStarted.emit)
            self._manager.pickingFinished.connect(self.pickingFinished.emit)
            self._manager.pickingCancelled.connect(self.pickingCancelled.emit)
            self._connected = True
        return self._manager

    @Slot(bool)
    def startPicking(self, is_dark: bool = False):
        self._ensure_manager().startPicking(is_dark)

    @Slot()
    def stopPicking(self):
        if self._manager is not None:
            self._manager.stopPicking()


__all__ = [
    "LazyQRCodeGenerator",
    "LazyScreenEyedropperManager",
]
