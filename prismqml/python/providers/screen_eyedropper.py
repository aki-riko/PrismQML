# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是FluentQML的一部分，采用MIT许可证授权。
"""ScreenEyedropper - Screen eyedropper color picker 屏幕取色器

Provides a magnifier window that follows the mouse cursor and picks colors from screen.
提供一个跟随鼠标的放大镜窗口，从屏幕上取色。
"""

from typing import Optional
from PySide6.QtCore import (
    QObject, Signal, Property, Slot, QTimer, QPoint, QRect, Qt, QSize
)
from PySide6.QtGui import (
    QColor, QScreen, QGuiApplication, QPainter, QPixmap, QImage,
    QPen, QBrush, QFont, QCursor
)
from PySide6.QtWidgets import QWidget, QApplication

from ..core import getLogger

logger = getLogger()


class ScreenEyedropperConstants:
    """Constants for ScreenEyedropper 屏幕取色器常量"""
    # Window size 窗口尺寸
    WINDOW_WIDTH = 122
    WINDOW_HEIGHT = 66
    
    # Preview area 预览区域
    PREVIEW_SIZE = 42
    PREVIEW_MARGIN = 8
    PREVIEW_RADIUS = 6
    PREVIEW_BORDER = 1
    
    # Magnifier 放大镜
    MAGNIFIER_SCALE = 8
    CAPTURE_SIZE = 15  # Odd number for center pixel 奇数以便有中心像素
    
    # Text 文字
    FONT_SIZE = 13
    TEXT_MARGIN = 8
    
    # Colors 颜色
    BORDER_COLOR_LIGHT = "#e0e0e0"
    BORDER_COLOR_DARK = "#404040"
    BG_COLOR_LIGHT = "#ffffff"
    BG_COLOR_DARK = "#2d2d2d"
    TEXT_COLOR_LIGHT = "#1a1a1a"
    TEXT_COLOR_DARK = "#ffffff"
    
    # Crosshair 十字准星
    CROSSHAIR_SIZE = 1
    CROSSHAIR_COLOR = "#ff0000"
    
    # Timer interval 定时器间隔
    # 不绑死 60fps; start_picking 时动态从屏幕刷新率算 interval(120Hz=8ms, 240Hz=4ms)
    # 拿不到刷新率时 fallback 到 16ms
    UPDATE_INTERVAL_FALLBACK_MS = 16
    
    # Window offset from cursor 窗口相对鼠标的偏移
    CURSOR_OFFSET_X = 16
    CURSOR_OFFSET_Y = 16


class ScreenEyedropperWindow(QWidget):
    """Magnifier window that follows cursor 跟随鼠标的放大镜窗口"""
    
    colorPicked = Signal(QColor)
    cancelled = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | 
                        Qt.WindowType.WindowStaysOnTopHint |
                        Qt.WindowType.Tool)
        self._constants = ScreenEyedropperConstants
        self._current_color = QColor(Qt.GlobalColor.white)
        self._is_dark = False
        self._captured_image: Optional[QImage] = None
        
        self._setup_window()
        self._setup_timer()
        
    def _setup_window(self):
        """Setup window properties 设置窗口属性"""
        self.setFixedSize(self._constants.WINDOW_WIDTH, self._constants.WINDOW_HEIGHT)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
    def _setup_timer(self):
        """Setup update timer 设置更新定时器"""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_position_and_color)
        
    def start_picking(self, is_dark: bool = False):
        """Start color picking 开始取色"""
        self._is_dark = is_dark
        self.show()
        self.raise_()
        self.activateWindow()
        mouse_grabbed = False
        keyboard_grabbed = False
        try:
            self.grabMouse()
            mouse_grabbed = True
            self.grabKeyboard()
            keyboard_grabbed = True
        except Exception:
            # 仅释放已成功抓取的资源，避免二次异常
            if keyboard_grabbed:
                self.releaseKeyboard()
            if mouse_grabbed:
                self.releaseMouse()
            self.hide()
            return
        # 跟随当前屏幕刷新率: 120Hz/144Hz/240Hz 高刷屏自动获得更平滑的取色追踪
        screen = self.screen() if hasattr(self, 'screen') else None
        refresh_rate = screen.refreshRate() if screen else 0
        if refresh_rate and refresh_rate > 0:
            interval_ms = max(1, int(round(1000.0 / refresh_rate)))
        else:
            interval_ms = self._constants.UPDATE_INTERVAL_FALLBACK_MS
        self._timer.start(interval_ms)
        self._update_position_and_color()
        
    def stop_picking(self):
        """Stop color picking 停止取色"""
        self._timer.stop()
        try:
            self.releaseMouse()
            self.releaseKeyboard()
        except Exception:
            pass
        self.hide()
        
    def _update_position_and_color(self):
        """Update window position and capture color 更新窗口位置并捕获颜色"""
        cursor_pos = QCursor.pos()
        
        # Position window near cursor 将窗口放在鼠标附近
        screen = QGuiApplication.screenAt(cursor_pos)
        if not screen:
            screen = QGuiApplication.primaryScreen()
            
        screen_geo = screen.geometry()
        
        # Calculate window position 计算窗口位置
        win_x = cursor_pos.x() + self._constants.CURSOR_OFFSET_X
        win_y = cursor_pos.y() + self._constants.CURSOR_OFFSET_Y
        
        # Keep window on screen 保持窗口在屏幕内
        if win_x + self.width() > screen_geo.right():
            win_x = cursor_pos.x() - self.width() - self._constants.CURSOR_OFFSET_X
        if win_y + self.height() > screen_geo.bottom():
            win_y = cursor_pos.y() - self.height() - self._constants.CURSOR_OFFSET_Y
            
        self.move(win_x, win_y)
        
        # Capture screen area around cursor 捕获鼠标周围的屏幕区域
        self._capture_screen(cursor_pos, screen)
        
        # Get center pixel color 获取中心像素颜色
        if self._captured_image and not self._captured_image.isNull():
            center = self._constants.CAPTURE_SIZE // 2
            self._current_color = QColor(self._captured_image.pixel(center, center))
            
        self.update()
        
    def _capture_screen(self, cursor_pos: QPoint, screen: QScreen):
        """Capture screen area around cursor 捕获鼠标周围的屏幕区域"""
        capture_size = self._constants.CAPTURE_SIZE
        half_size = capture_size // 2
        
        # Calculate capture rect 计算捕获区域
        capture_rect = QRect(
            cursor_pos.x() - half_size,
            cursor_pos.y() - half_size,
            capture_size,
            capture_size
        )
        
        # Capture screen 截取屏幕
        pixmap = screen.grabWindow(
            0,  # Window ID 0 = entire screen
            capture_rect.x(),
            capture_rect.y(),
            capture_rect.width(),
            capture_rect.height()
        )
        
        self._captured_image = pixmap.toImage()
        
    def paintEvent(self, event):
        """Paint the magnifier window 绘制放大镜窗口"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        c = self._constants
        
        # Background colors 背景颜色
        bg_color = QColor(c.BG_COLOR_DARK if self._is_dark else c.BG_COLOR_LIGHT)
        border_color = QColor(c.BORDER_COLOR_DARK if self._is_dark else c.BORDER_COLOR_LIGHT)
        text_color = QColor(c.TEXT_COLOR_DARK if self._is_dark else c.TEXT_COLOR_LIGHT)
        
        # Draw background 绘制背景
        painter.setPen(QPen(border_color, c.PREVIEW_BORDER))
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(
            self.rect().adjusted(0, 0, -1, -1),
            c.PREVIEW_RADIUS, c.PREVIEW_RADIUS
        )
        
        # Draw color preview square 绘制颜色预览方块
        preview_rect = QRect(
            c.PREVIEW_MARGIN,
            (self.height() - c.PREVIEW_SIZE) // 2,
            c.PREVIEW_SIZE,
            c.PREVIEW_SIZE
        )
        
        # Draw magnified pixels if available 绘制放大的像素
        if self._captured_image and not self._captured_image.isNull():
            # Scale up the captured image 放大捕获的图像
            scaled = self._captured_image.scaled(
                c.PREVIEW_SIZE, c.PREVIEW_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation
            )
            painter.drawImage(preview_rect.topLeft(), scaled)
            
            # Draw crosshair at center 在中心绘制十字准星
            center_x = preview_rect.x() + c.PREVIEW_SIZE // 2
            center_y = preview_rect.y() + c.PREVIEW_SIZE // 2
            pixel_size = c.PREVIEW_SIZE // c.CAPTURE_SIZE
            
            painter.setPen(QPen(QColor(c.CROSSHAIR_COLOR), c.CROSSHAIR_SIZE))
            # Horizontal line 水平线
            painter.drawLine(
                preview_rect.left(), center_y,
                preview_rect.right(), center_y
            )
            # Vertical line 垂直线
            painter.drawLine(
                center_x, preview_rect.top(),
                center_x, preview_rect.bottom()
            )
        else:
            # Fallback: draw solid color 回退：绘制纯色
            painter.setBrush(QBrush(self._current_color))
            painter.drawRoundedRect(preview_rect, c.PREVIEW_RADIUS // 2, c.PREVIEW_RADIUS // 2)
        
        # Draw preview border 绘制预览边框
        painter.setPen(QPen(border_color, c.PREVIEW_BORDER))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(preview_rect, c.PREVIEW_RADIUS // 2, c.PREVIEW_RADIUS // 2)
        
        # Draw hex color text 绘制HEX颜色文字
        hex_text = self._current_color.name().upper()
        font = QFont()
        font.setPixelSize(c.FONT_SIZE)
        font.setFamily("Segoe UI")
        painter.setFont(font)
        painter.setPen(text_color)
        
        text_x = preview_rect.right() + c.TEXT_MARGIN
        text_y = self.height() // 2 + c.FONT_SIZE // 3
        painter.drawText(text_x, text_y, hex_text)
        
    def mousePressEvent(self, event):
        """Handle mouse press - pick color 处理鼠标按下 - 取色"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.colorPicked.emit(self._current_color)
            self.stop_picking()
        elif event.button() == Qt.MouseButton.RightButton:
            self.cancelled.emit()
            self.stop_picking()
            
    def keyPressEvent(self, event):
        """Handle key press - ESC to cancel 处理按键 - ESC取消"""
        if event.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()
            self.stop_picking()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.colorPicked.emit(self._current_color)
            self.stop_picking()
            
    def focusOutEvent(self, event):
        """Handle focus lost - cancel picking 处理失焦 - 取消取色"""
        self.cancelled.emit()
        self.stop_picking()
        super().focusOutEvent(event)


class ScreenEyedropperManager(QObject):
    """Manager for screen color picking 屏幕取色管理器
    
    Singleton that manages the picker window and provides QML interface.
    单例模式，管理取色窗口并提供QML接口。
    """
    
    # Signals 信号
    colorPicked = Signal(QColor)
    pickingStarted = Signal()
    pickingFinished = Signal()
    pickingCancelled = Signal()
    
    _instance: Optional["ScreenEyedropperManager"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        super().__init__()
        self._initialized = True
        self._picker_window: Optional[ScreenEyedropperWindow] = None
        self._is_dark = False
        logger.debug("ScreenEyedropperManager initialized 屏幕取色管理器已初始化")
        
    def _ensure_window(self):
        """Ensure picker window exists 确保取色窗口存在"""
        if self._picker_window is None:
            self._picker_window = ScreenEyedropperWindow()
            self._picker_window.colorPicked.connect(self._on_color_picked)
            self._picker_window.cancelled.connect(self._on_cancelled)
            
    def _on_color_picked(self, color: QColor):
        """Handle color picked 处理颜色选取"""
        logger.debug(f"Color picked: {color.name()} 已选取颜色")
        self.colorPicked.emit(color)
        self.pickingFinished.emit()
        
    def _on_cancelled(self):
        """Handle picking cancelled 处理取消取色"""
        logger.debug("Color picking cancelled 取色已取消")
        self.pickingCancelled.emit()
        self.pickingFinished.emit()
        
    @Slot(bool)
    def startPicking(self, is_dark: bool = False):
        """Start screen color picking 开始屏幕取色
        
        Args:
            is_dark: Whether to use dark theme for picker window
        """
        self._ensure_window()
        self._is_dark = is_dark
        self._picker_window.start_picking(is_dark)
        self.pickingStarted.emit()
        logger.debug("Screen color picking started 屏幕取色已开始")
        
    @Slot()
    def stopPicking(self):
        """Stop screen color picking 停止屏幕取色"""
        if self._picker_window:
            self._picker_window.stop_picking()
            self.pickingFinished.emit()
            logger.debug("Screen color picking stopped 屏幕取色已停止")


def get_screen_eyedropper_manager() -> ScreenEyedropperManager:
    """获取屏幕取色管理器单例 Get the singleton ScreenEyedropperManager instance"""
    return ScreenEyedropperManager()


__all__ = [
    "ScreenEyedropperManager",
    "ScreenEyedropperWindow", 
    "ScreenEyedropperConstants",
    "get_screen_eyedropper_manager",
]
