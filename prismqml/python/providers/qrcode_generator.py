# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是FluentQML的一部分，采用MIT许可证授权。
"""QRCode Generator - 二维码生成器"""

from typing import List, Optional
from PySide6.QtCore import QObject, Signal, Property, Slot
from PySide6.QtGui import QImage, QColor
from PySide6.QtQuick import QQuickImageProvider

from ..core import error

try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False


class QRCodeImageProvider(QQuickImageProvider):
    """QML图片提供器 - 生成二维码图片"""
    
    # 最大缓存条目数 Maximum cache entries
    MAX_CACHE_SIZE = 128
    
    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._cache = {}
    
    def requestImage(self, id: str, size, requestedSize):
        """
        请求二维码图片
        id格式: content|size|fgColor|bgColor|errorCorrection
        例如: Hello World|150|#000000|#ffffff|M
        
        Returns: QImage
        """
        if not HAS_QRCODE:
            return self._create_placeholder(requestedSize)
        
        # 解析参数
        parts = id.split("|")
        content = parts[0] if len(parts) > 0 else ""
        target_size = int(parts[1]) if len(parts) > 1 else 150
        fg_color = parts[2] if len(parts) > 2 else "#000000"
        bg_color = parts[3] if len(parts) > 3 else "#ffffff"
        error_level = parts[4] if len(parts) > 4 else "M"
        
        if not content:
            return self._create_placeholder(requestedSize)
        
        # 缓存key
        cache_key = f"{content}|{target_size}|{fg_color}|{bg_color}|{error_level}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 生成二维码
        try:
            img = self._generate_qrcode(content, target_size, fg_color, bg_color, error_level)
            # 缓存限制：超出时清除最早的一半 Evict oldest half when exceeding limit
            if len(self._cache) >= self.MAX_CACHE_SIZE:
                keys_to_remove = list(self._cache.keys())[: self.MAX_CACHE_SIZE // 2]
                for k in keys_to_remove:
                    del self._cache[k]
            self._cache[cache_key] = img
            return img
        except Exception as e:
            error(f"生成失败: {e}")
            return self._create_placeholder(requestedSize)
    
    def _generate_qrcode(self, content: str, size: int, fg_color: str, bg_color: str, error_level: str) -> QImage:
        """生成二维码QImage"""
        # 错误纠正级别映射
        error_map = {
            "L": ERROR_CORRECT_L,  # 7%
            "M": ERROR_CORRECT_M,  # 15%
            "Q": ERROR_CORRECT_Q,  # 25%
            "H": ERROR_CORRECT_H,  # 30%
        }
        error_correction = error_map.get(error_level.upper(), ERROR_CORRECT_M)
        
        # 创建二维码
        qr = qrcode.QRCode(
            version=None,  # 自动选择版本
            error_correction=error_correction,
            box_size=1,  # 每个模块1像素，后面缩放
            border=2,  # 边框2个模块
        )
        qr.add_data(content)
        qr.make(fit=True)
        
        # 获取矩阵
        matrix = qr.get_matrix()
        modules = len(matrix)
        
        # 计算模块大小以适应目标尺寸
        module_size = max(1, size // modules)
        actual_size = modules * module_size
        
        # 创建QImage
        image = QImage(actual_size, actual_size, QImage.Format.Format_RGB32)
        
        # 解析颜色
        fg = QColor(fg_color)
        bg = QColor(bg_color)
        
        # 填充背景
        image.fill(bg)
        
        # 使用 QPainter.fillRect 批量绘制模块（比逐像素 setPixelColor 快数十倍）
        from PySide6.QtCore import QRect
        from PySide6.QtGui import QPainter
        painter = QPainter(image)
        painter.setPen(fg)
        painter.setBrush(fg)
        for row in range(modules):
            for col in range(modules):
                if matrix[row][col]:
                    painter.fillRect(
                        QRect(col * module_size, row * module_size, module_size, module_size),
                        fg
                    )
        painter.end()
        
        # 缩放到目标尺寸
        if actual_size != size:
            image = image.scaled(size, size)
        
        return image
    
    def _create_placeholder(self, size) -> QImage:
        """创建占位图"""
        s = size.width() if size and size.width() > 0 else 150
        image = QImage(s, s, QImage.Format.Format_RGB32)
        image.fill(QColor("#f0f0f0"))
        return image
    
    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()


class QRCodeGenerator(QObject):
    """二维码生成器 - 暴露给QML的接口"""
    
    availableChanged = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    @Property(bool, notify=availableChanged)
    def available(self) -> bool:
        """检查qrcode库是否可用"""
        return HAS_QRCODE
    
    @Slot(str, int, str, str, str, result=str)
    def getImageSource(self, content: str, size: int = 150, 
                       fgColor: str = "#000000", bgColor: str = "#ffffff",
                       errorLevel: str = "M") -> str:
        """
        获取二维码图片源URL
        
        Args:
            content: 二维码内容
            size: 目标尺寸（像素）
            fgColor: 前景色（黑色模块）
            bgColor: 背景色
            errorLevel: 错误纠正级别 L/M/Q/H
        
        Returns:
            图片源URL，格式: image://qrcode/content|size|fg|bg|level
        """
        # URL编码content中的特殊字符
        safe_content = content.replace("|", "%7C")
        return f"image://qrcode/{safe_content}|{size}|{fgColor}|{bgColor}|{errorLevel}"


# 全局实例
_qrcode_generator: Optional[QRCodeGenerator] = None
_qrcode_provider: Optional[QRCodeImageProvider] = None


def get_qrcode_generator() -> QRCodeGenerator:
    """获取二维码生成器单例"""
    global _qrcode_generator
    if _qrcode_generator is None:
        _qrcode_generator = QRCodeGenerator()
    return _qrcode_generator


def get_qrcode_provider() -> QRCodeImageProvider:
    """获取二维码图片提供器单例"""
    global _qrcode_provider
    if _qrcode_provider is None:
        _qrcode_provider = QRCodeImageProvider()
    return _qrcode_provider
