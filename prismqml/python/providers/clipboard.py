# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是FluentQML的一部分，采用MIT许可证授权。
"""
Clipboard Helper - 剪贴板工具类

提供剪贴板读写功能，供QML调用。
"""

from typing import Optional

from PySide6.QtCore import QObject, Slot
from PySide6.QtGui import QGuiApplication


class ClipboardHelper(QObject):
    """剪贴板工具类 Clipboard helper class"""
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
    
    @Slot(str)
    def copy(self, text: str) -> None:
        """复制文本到剪贴板 Copy text to clipboard"""
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(text)
    
    @Slot(result=str)
    def paste(self) -> str:
        """从剪贴板粘贴文本 Paste text from clipboard"""
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            return clipboard.text()
        return ""


# 单例实例 Singleton instance
_clipboard_helper: Optional[ClipboardHelper] = None


def get_clipboard_helper() -> ClipboardHelper:
    """获取剪贴板工具单例 Get clipboard helper singleton"""
    global _clipboard_helper
    if _clipboard_helper is None:
        _clipboard_helper = ClipboardHelper()
    return _clipboard_helper
