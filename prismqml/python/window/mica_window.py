# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是FluentQML的一部分，采用MIT许可证授权。
"""
Mica Effect Manager & Acrylic Helper 云母效果管理器 & 亚克力助手

Provides Windows 11 Mica backdrop effect and Acrylic blur for FluentQML windows.
为 FluentQML 窗口提供 Windows 11 云母背景效果和亚克力模糊。
"""
import sys
from typing import Optional
from PySide6.QtCore import QObject, Signal, Slot, Property, QRect, QSize, QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QWindow, QImage, QColor, QPainter, QPixmap
from PySide6.QtWidgets import QApplication
from PySide6.QtQuick import QQuickImageProvider

from ..core.logger import info, warning, error, debug

# Windows 11 build number threshold Windows 11 版本号阈值
WIN11_BUILD_THRESHOLD = 22000

# DWMWA_SYSTEMBACKDROP_TYPE 最低支持版本（Win11 22H2）
# Build 22000-22621 之间无此接口，调用会静默失败
WIN11_BACKDROP_BUILD_THRESHOLD = 22621

# DWM constants DWM 常量
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWA_SYSTEMBACKDROP_TYPE = 38  # 需要 Build >= 22621

# Window corner preference 窗口圆角偏好
DWMWCP_ROUND = 2

# DWM backdrop type values DWM背景类型值
DWM_BACKDROP_NONE = 1   # DWMSBT_NONE
DWM_BACKDROP_MICA = 2   # DWMSBT_MAINWINDOW (Mica)


def _is_win11() -> bool:
    """Check if running on Windows 11 检查是否运行在 Windows 11"""
    if sys.platform != "win32":
        return False
    try:
        return sys.getwindowsversion().build >= WIN11_BUILD_THRESHOLD
    except AttributeError:
        return False


def _get_dwm_set_attr():
    """Get DwmSetWindowAttribute function 获取 DwmSetWindowAttribute 函数"""
    if sys.platform != "win32":
        return None
    
    try:
        import ctypes
        from ctypes import wintypes
        
        dwmapi = ctypes.windll.dwmapi
        dwm_set_attr = dwmapi.DwmSetWindowAttribute
        dwm_set_attr.argtypes = [
            wintypes.HWND,
            wintypes.DWORD,
            ctypes.c_void_p,
            wintypes.DWORD
        ]
        dwm_set_attr.restype = ctypes.HRESULT
        return dwm_set_attr
    except (ImportError, AttributeError, OSError) as e:
        warning(f"Failed to load DWM API: {e}")
        return None


class MicaManager(QObject):
    """
    Mica Effect Manager 云母效果管理器
    
    Manages Windows 11 Mica backdrop effect for QML windows.
    管理 QML 窗口的 Windows 11 云母背景效果。
    """
    
    micaEnabledChanged = Signal(bool)
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._mica_enabled = False
        self._is_win11 = _is_win11()
        self._dwm_set_attr = _get_dwm_set_attr()
        self._current_hwnd: Optional[int] = None
        self._current_window: Optional[QWindow] = None
    
    @Property(bool, constant=True)
    def isWin11(self) -> bool:
        """Check if running on Windows 11 检查是否运行在 Windows 11"""
        return self._is_win11
    
    @Property(bool, notify=micaEnabledChanged)
    def micaEnabled(self) -> bool:
        """Get mica effect enabled state 获取云母效果启用状态"""
        return self._mica_enabled
    
    def _applyMica(self, window: QWindow, enabled: bool) -> bool:
        """Internal: Apply mica effect 内部方法：应用云母效果"""
        if not self._is_win11 or not self._dwm_set_attr:
            return False
        
        try:
            import ctypes
            
            hwnd = int(window.winId())
            if not hwnd:
                return False
            
            self._current_hwnd = hwnd
            
            # Set window corner to round 设置窗口圆角
            corner_pref = ctypes.c_int(DWMWCP_ROUND)
            self._dwm_set_attr(
                hwnd,
                DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(corner_pref),
                ctypes.sizeof(corner_pref)
            )
            
            # Set backdrop type 设置背景类型
            # DWMWA_SYSTEMBACKDROP_TYPE (38) 需要 Win11 22H2 (Build 22621+)
            build = sys.getwindowsversion().build
            if build < WIN11_BACKDROP_BUILD_THRESHOLD:
                warning(f"DWMWA_SYSTEMBACKDROP_TYPE requires Build >= {WIN11_BACKDROP_BUILD_THRESHOLD}, current: {build}")
                return False
            
            backdrop_value = ctypes.c_int(DWM_BACKDROP_MICA if enabled else DWM_BACKDROP_NONE)
            result = self._dwm_set_attr(
                hwnd,
                DWMWA_SYSTEMBACKDROP_TYPE,
                ctypes.byref(backdrop_value),
                ctypes.sizeof(backdrop_value)
            )
            
            if result == 0:
                info(f"Mica effect {'enabled' if enabled else 'disabled'}")
                return True
            else:
                warning(f"DwmSetWindowAttribute failed: {result}")
                return False
                
        except (ValueError, OSError, TypeError) as e:
            error(f"Failed to apply mica: {e}")
            return False
    
    @Slot(QWindow, bool, bool, result=bool)
    def setMicaEffect(self, window: QWindow, enabled: bool, dark: bool = False) -> bool:
        """
        Set mica effect for a window 为窗口设置云母效果
        
        Args:
            window: Target QWindow 目标窗口
            enabled: Enable mica effect 启用云母效果
            dark: Use dark mode 使用深色模式
            
        Returns:
            True if successful 成功返回 True
        """
        if not self._is_win11 or not self._dwm_set_attr:
            debug("Mica effect not available (not Win11 or DWM unavailable)")
            return False
        
        if not window:
            warning("Cannot set mica effect: window is None")
            return False
        
        try:
            import ctypes
            
            self._current_window = window
            self._current_hwnd = int(window.winId())
            
            # Set dark mode 设置深色模式
            dark_value = ctypes.c_int(1 if dark else 0)
            self._dwm_set_attr(
                self._current_hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(dark_value),
                ctypes.sizeof(dark_value)
            )
            
            # Apply mica 应用云母效果
            success = self._applyMica(window, enabled)
            
            if success:
                self._mica_enabled = enabled
                self.micaEnabledChanged.emit(enabled)
            
            return success
                
        except (ValueError, OSError, TypeError) as e:
            error(f"Failed to set mica effect: {e}")
            return False
    
    @Slot(bool)
    def updateDarkMode(self, dark: bool):
        """
        Update dark mode for current window 更新当前窗口的深色模式
        
        Args:
            dark: Use dark mode 使用深色模式
        """
        if not self._is_win11 or not self._dwm_set_attr or not self._current_hwnd:
            return
        
        try:
            import ctypes
            
            dark_value = ctypes.c_int(1 if dark else 0)
            self._dwm_set_attr(
                self._current_hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(dark_value),
                ctypes.sizeof(dark_value)
            )
            debug(f"Dark mode updated: {dark}")
            
        except (ValueError, OSError, TypeError) as e:
            error(f"Failed to update dark mode: {e}")


# Singleton instance 单例实例
_mica_manager: Optional[MicaManager] = None


def get_mica_manager() -> MicaManager:
    """Get the singleton MicaManager instance 获取 MicaManager 单例"""
    global _mica_manager
    if _mica_manager is None:
        _mica_manager = MicaManager()
    return _mica_manager


# ==================== Acrylic Helper 亚克力助手 ====================

# Acrylic constants 亚克力常量
ACRYLIC_BLUR_RADIUS = 100


def _gaussian_blur_image(image: QImage, radius: int) -> QImage:
    """
    Apply blur to QImage using Qt's built-in scaling (no external dependencies)
    使用Qt内置缩放实现模糊（无外部依赖）
    
    Scale down then up approach provides good blur effect with zero dependencies.
    缩小再放大的方法可以提供良好的模糊效果，且无需任何依赖。
    """
    from PySide6.QtCore import Qt
    
    if image.isNull() or radius <= 0:
        return image
    
    # Convert to ARGB32 for processing 转换为 ARGB32 处理
    img = image.convertToFormat(QImage.Format.Format_ARGB32)
    width, height = img.width(), img.height()
    
    if width == 0 or height == 0:
        return image
    
    # Use scale down/up approach - fast and no dependencies
    # 使用缩小/放大方法 - 快速且无依赖
    # Scale factor based on blur radius 根据模糊半径计算缩放因子
    scale_factor = max(2, radius // 4)
    
    # Scale down 缩小
    small_w = max(1, width // scale_factor)
    small_h = max(1, height // scale_factor)
    
    # Use QPixmap for better quality scaling 使用QPixmap获得更好的缩放质量
    pixmap = QPixmap.fromImage(img)
    small = pixmap.scaled(small_w, small_h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
    
    # Scale back up 放大回来
    result_pixmap = small.scaled(width, height, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
    
    return result_pixmap.toImage()


class AcrylicImageProvider(QQuickImageProvider):
    """
    Image provider for acrylic blurred background
    亚克力模糊背景图片提供器
    
    Provides blurred screenshot for QML acrylic effect.
    为 QML 亚克力效果提供模糊截图。
    """
    
    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._current_image: Optional[QImage] = None
        self._image_id = 0
    
    def requestImage(self, id: str, size: QSize, requestedSize: QSize) -> QImage:
        """Provide the blurred image to QML 向 QML 提供模糊图片"""
        if self._current_image is None or self._current_image.isNull():
            # Return transparent placeholder 返回透明占位图
            placeholder = QImage(1, 1, QImage.Format.Format_ARGB32)
            placeholder.fill(QColor(0, 0, 0, 0))
            return placeholder
        
        img = self._current_image
        if requestedSize.isValid() and requestedSize.width() > 0 and requestedSize.height() > 0:
            img = img.scaled(requestedSize, mode=1)  # SmoothTransformation
        
        return img
    
    def setImage(self, image: QImage):
        """Set the current blurred image 设置当前模糊图片"""
        self._current_image = image
        self._image_id += 1
    
    @property
    def currentImageId(self) -> int:
        """Get current image ID for cache busting 获取当前图片ID用于缓存刷新"""
        return self._image_id


class AcrylicHelper(QObject):
    """
    Acrylic Effect Helper 亚克力效果助手
    
    Captures screen region and applies blur for acrylic effect.
    截取屏幕区域并应用模糊实现亚克力效果。
    
    Uses Qt's built-in scaling for blur - no external dependencies (numpy/scipy).
    使用Qt内置缩放实现模糊 - 无外部依赖（numpy/scipy）。
    """
    
    imageReady = Signal(str)  # Emits image source URL 发射图片源URL
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._image_provider = AcrylicImageProvider()
        self._blur_radius = ACRYLIC_BLUR_RADIUS
        self._is_available = True
    
    @Property(bool, constant=True)
    def isAvailable(self) -> bool:
        """Check if acrylic effect is available 检查亚克力效果是否可用"""
        return self._is_available
    
    @Property(int)
    def blurRadius(self) -> int:
        """Get blur radius 获取模糊半径"""
        return self._blur_radius
    
    @blurRadius.setter
    def blurRadius(self, value: int):
        """Set blur radius 设置模糊半径"""
        self._blur_radius = max(1, min(100, value))
    
    @property
    def imageProvider(self) -> AcrylicImageProvider:
        """Get the image provider for QML engine registration 获取图片提供器用于 QML 引擎注册"""
        return self._image_provider
    
    @Slot(QWindow, int, int, int, int, result=str)
    def grabAndBlur(self, window: QWindow, x: int, y: int, width: int, height: int) -> str:
        """
        Grab screen region and apply blur 截取屏幕区域并应用模糊
        
        Args:
            window: Source window for coordinate mapping 用于坐标映射的源窗口
            x: X position relative to window 相对于窗口的X位置
            y: Y position relative to window 相对于窗口的Y位置
            width: Region width 区域宽度
            height: Region height 区域高度
            
        Returns:
            Image source URL for QML 用于 QML 的图片源URL
        """
        if not window or width <= 0 or height <= 0:
            warning("Invalid parameters for grabAndBlur")
            return ""
        
        try:
            # Get screen 获取屏幕
            screen = window.screen()
            if not screen:
                screens = QApplication.screens()
                if screens:
                    screen = screens[0]
                else:
                    error("No screen available")
                    return ""
            
            # Get window global position 获取窗口全局位置
            # QWindow.position() returns position relative to screen
            # QWindow.position() 返回相对于屏幕的位置
            win_x = window.x()
            win_y = window.y()
            
            # Calculate global coordinates 计算全局坐标
            global_x = win_x + x
            global_y = win_y + y
            
            # Adjust for screen offset (for multi-monitor) 调整屏幕偏移（多显示器）
            screen_geo = screen.geometry()
            grab_x = global_x - screen_geo.x()
            grab_y = global_y - screen_geo.y()
            
            # Grab screen region (0 = entire desktop, includes Mica effect)
            # 截取屏幕区域（0 = 整个桌面，包含云母效果）
            pixmap = screen.grabWindow(0, grab_x, grab_y, width, height)
            if pixmap.isNull():
                error("Failed to grab screen")
                return ""
            
            # Convert to QImage and blur 转换为 QImage 并模糊
            image = pixmap.toImage()
            blurred = _gaussian_blur_image(image, self._blur_radius)
            
            # Store in provider 存储到提供器
            self._image_provider.setImage(blurred)
            
            # Return image URL with cache-busting ID 返回带缓存刷新ID的图片URL
            image_url = f"image://acrylic/{self._image_provider.currentImageId}"
            self.imageReady.emit(image_url)
            
            debug(f"Acrylic image ready: {width}x{height}")
            return image_url
            
        except (ValueError, OSError, RuntimeError) as e:
            error(f"Failed to grab and blur: {e}")
            return ""
    
    @Slot(result=str)
    def getImageUrl(self) -> str:
        """Get current image URL 获取当前图片URL"""
        return f"image://acrylic/{self._image_provider.currentImageId}"


# Singleton instances 单例实例
_acrylic_helper: Optional[AcrylicHelper] = None


def get_acrylic_helper() -> AcrylicHelper:
    """Get the singleton AcrylicHelper instance 获取 AcrylicHelper 单例"""
    global _acrylic_helper
    if _acrylic_helper is None:
        _acrylic_helper = AcrylicHelper()
    return _acrylic_helper
