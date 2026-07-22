# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""
Mica Effect Manager & Acrylic Helper 云母效果管理器 & 亚克力助手

Provides Windows 11 Mica backdrop effect and Acrylic blur for PrismQML windows.
为 PrismQML 窗口提供 Windows 11 云母背景效果和亚克力模糊。
"""
import sys
from threading import Lock
from typing import Any, Optional
from PySide6.QtCore import (
    QByteArray,
    QBuffer,
    QIODevice,
    QObject,
    Property,
    QRect,
    QSize,
    Signal,
    Slot,
    Qt,
)
from PySide6.QtGui import QWindow, QImage, QColor, QPainter, QPixmap, QScreen
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
DWMWCP_DONOTROUND = 1
DWMWCP_ROUND = 2

# DWM backdrop type values DWM背景类型值
DWM_BACKDROP_NONE = 1   # DWMSBT_NONE
DWM_BACKDROP_MICA = 2   # DWMSBT_MAINWINDOW (Mica)


def _dwm_hresult_succeeded(result: int) -> bool:
    """Apply Windows SUCCEEDED semantics. 使用 Windows SUCCEEDED 语义。"""
    return int(result) >= 0


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
        self._windows_build = sys.getwindowsversion().build if sys.platform == "win32" else 0
        self._is_mica_supported = (
            self._is_win11
            and self._dwm_set_attr is not None
            and self._windows_build >= WIN11_BACKDROP_BUILD_THRESHOLD
        )
        self._current_hwnd: Optional[int] = None
        self._current_window: Optional[QWindow] = None
    
    @Property(bool, constant=True)
    def isWin11(self) -> bool:
        """Check if running on Windows 11 检查是否运行在 Windows 11"""
        return self._is_win11

    @Property(bool, constant=True)
    def isMicaSupported(self) -> bool:
        """Check if DWM system backdrop Mica is supported 检查 DWM 云母背板是否可用"""
        return self._is_mica_supported
    
    @Property(bool, notify=micaEnabledChanged)
    def micaEnabled(self) -> bool:
        """Get mica effect enabled state 获取云母效果启用状态"""
        return self._mica_enabled
    
    def _set_dwm_int_attribute(self, hwnd: int, attribute: int, value: int) -> int:
        """Set one integer DWM attribute. 设置单个整数 DWM 属性。"""
        import ctypes

        native_value = ctypes.c_int(value)
        return self._dwm_set_attr(
            hwnd,
            attribute,
            ctypes.byref(native_value),
            ctypes.sizeof(native_value),
        )

    def _apply_mica_to_hwnd(self, hwnd: int, enabled: bool) -> bool:
        """Apply rounded Mica backdrop to a validated HWND. 向已验证 HWND 应用云母。"""
        if self._windows_build < WIN11_BACKDROP_BUILD_THRESHOLD:
            warning(
                "DWMWA_SYSTEMBACKDROP_TYPE requires Build >= "
                f"{WIN11_BACKDROP_BUILD_THRESHOLD}, current: {self._windows_build}"
            )
            return False
        self._set_dwm_int_attribute(
            hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, DWMWCP_ROUND
        )
        backdrop = DWM_BACKDROP_MICA if enabled else DWM_BACKDROP_NONE
        result = self._set_dwm_int_attribute(
            hwnd, DWMWA_SYSTEMBACKDROP_TYPE, backdrop
        )
        if _dwm_hresult_succeeded(result):
            info(f"Mica effect {'enabled' if enabled else 'disabled'}")
            return True
        warning(f"DwmSetWindowAttribute failed: {result}")
        return False

    def _applyMica(self, window: QWindow, enabled: bool) -> bool:
        """Internal: Apply mica effect 内部方法：应用云母效果"""
        if not self._is_mica_supported:
            return False
        try:
            hwnd = int(window.winId())
            if not hwnd:
                return False
            return self._apply_mica_to_hwnd(hwnd, enabled)
        except (ValueError, OSError, TypeError) as e:
            error(f"Failed to apply mica: {e}")
            return False

    @Slot(QWindow, bool, result=bool)
    def setWindowCorner(self, window: QWindow, rounded: bool) -> bool:
        """Set corner preference without changing Mica state. 设置圆角但不改变 Mica 状态。"""
        if not self._is_win11 or self._dwm_set_attr is None or not window:
            return False
        try:
            hwnd = int(window.winId())
            if not hwnd:
                return False
            preference = DWMWCP_ROUND if rounded else DWMWCP_DONOTROUND
            result = self._set_dwm_int_attribute(
                hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, preference
            )
            return _dwm_hresult_succeeded(result)
        except (ValueError, OSError, TypeError) as e:
            error(f"Failed to set window corner: {e}")
            return False
    
    @Slot(QWindow, bool, bool, result=bool)
    def setMicaEffect(self, window: QWindow, enabled: bool, dark: bool = False) -> bool:
        """Set Mica and commit state after success. 设置云母并在成功后提交状态。"""
        if not self._is_mica_supported:
            debug("Mica effect not available (not Win11 or DWM unavailable)")
            return False
        
        if not window:
            warning("Cannot set mica effect: window is None")
            return False
        
        try:
            hwnd = int(window.winId())
            if not hwnd:
                warning("Cannot set mica effect: window HWND is empty")
                return False
            self._set_dwm_int_attribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, 1 if dark else 0
            )
            if not self._apply_mica_to_hwnd(hwnd, enabled):
                return False
            self._current_window = window
            self._current_hwnd = hwnd
            self._mica_enabled = enabled
            self.micaEnabledChanged.emit(enabled)
            return True
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
_NO_ACRYLIC_SCREEN = object()


def _scale_acrylic_image(
    image: QImage, width: int, height: int, radius: int, qt_namespace: Any
) -> QImage:
    """Scale an image down and back up. 缩小再放大图像。"""
    scale_factor = max(2, radius // 4)
    small_width = max(1, width // scale_factor)
    small_height = max(1, height // scale_factor)
    pixmap = QPixmap.fromImage(image)
    small = pixmap.scaled(
        small_width,
        small_height,
        qt_namespace.AspectRatioMode.IgnoreAspectRatio,
        qt_namespace.TransformationMode.SmoothTransformation,
    )
    result_pixmap = small.scaled(
        width,
        height,
        qt_namespace.AspectRatioMode.IgnoreAspectRatio,
        qt_namespace.TransformationMode.SmoothTransformation,
    )
    return result_pixmap.toImage()


def _gaussian_blur_image(image: QImage, radius: int) -> QImage:
    """Apply dependency-free scale blur. 使用无依赖缩放实现模糊。"""
    from PySide6.QtCore import Qt

    if image.isNull() or radius <= 0:
        return image
    converted = image.convertToFormat(QImage.Format.Format_ARGB32)
    width, height = converted.width(), converted.height()
    if width == 0 or height == 0:
        return image
    return _scale_acrylic_image(converted, width, height, radius, Qt)


def _resolve_acrylic_screen(window: QWindow) -> Any:
    """Resolve the capture screen or a private sentinel. 解析截图屏幕或私有哨兵。"""
    screen = window.screen()
    if not screen:
        screens = QApplication.screens()
        if screens:
            screen = screens[0]
        else:
            error("No screen available")
            return _NO_ACRYLIC_SCREEN
    return screen


def _grab_acrylic_region(
    window: QWindow, screen: QScreen, x: int, y: int, width: int, height: int
) -> QPixmap:
    """Capture a window-relative screen region. 截取窗口相对的屏幕区域。"""
    win_x = window.x()
    win_y = window.y()
    global_x = win_x + x
    global_y = win_y + y
    screen_geo = screen.geometry()
    grab_x = global_x - screen_geo.x()
    grab_y = global_y - screen_geo.y()
    return screen.grabWindow(0, grab_x, grab_y, width, height)


def _publish_acrylic_capture(owner: Any, pixmap: QPixmap, width: int, height: int) -> str:
    """Blur and publish one captured image. 模糊并发布一帧截图。"""
    image = pixmap.toImage()
    blurred = _gaussian_blur_image(image, owner._blur_radius)
    owner._image_state.set_image(blurred)
    image_url = f"image://acrylic/{owner._image_state.image_id}"
    owner.imageReady.emit(image_url)
    debug(f"Acrylic image ready: {width}x{height}")
    return image_url


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


class AcrylicImageProvider(QQuickImageProvider):
    """
    Image provider for acrylic blurred background
    亚克力模糊背景图片提供器
    
    Provides blurred screenshot for QML acrylic effect.
    为 QML 亚克力效果提供模糊截图。
    """
    
    def __init__(self, state: Optional[_AcrylicImageState] = None):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._state = state or _AcrylicImageState()
    
    def requestImage(self, id: str, size: QSize, requestedSize: QSize) -> QImage:
        """Provide the blurred image to QML 向 QML 提供模糊图片"""
        img = self._state.image()
        if img is None or img.isNull():
            # Return transparent placeholder 返回透明占位图
            placeholder = QImage(1, 1, QImage.Format.Format_ARGB32)
            placeholder.fill(QColor(0, 0, 0, 0))
            return placeholder

        if requestedSize.isValid() and requestedSize.width() > 0 and requestedSize.height() > 0:
            img = img.scaled(
                requestedSize,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        
        return img
    
    def setImage(self, image: QImage):
        """Set the current blurred image 设置当前模糊图片"""
        self._state.set_image(image)
    
    @property
    def currentImageId(self) -> int:
        """Get current image ID for cache busting 获取当前图片ID用于缓存刷新"""
        return self._state.image_id


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
        self._image_state = _AcrylicImageState()
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
        """Create an engine-owned provider adapter. 创建由引擎持有的 provider 适配器。"""
        return AcrylicImageProvider(self._image_state)
    
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
            screen = _resolve_acrylic_screen(window)
            if screen is _NO_ACRYLIC_SCREEN:
                return ""
            pixmap = _grab_acrylic_region(window, screen, x, y, width, height)
            if pixmap.isNull():
                error("Failed to grab screen")
                return ""
            return _publish_acrylic_capture(self, pixmap, width, height)
        except (ValueError, OSError, RuntimeError) as e:
            error(f"Failed to grab and blur: {e}")
            return ""
    
    @Slot(result=str)
    def getImageUrl(self) -> str:
        """Get current image URL 获取当前图片URL"""
        return f"image://acrylic/{self._image_state.image_id}"


# Singleton instances 单例实例
_acrylic_helper: Optional[AcrylicHelper] = None


def get_acrylic_helper() -> AcrylicHelper:
    """Get the singleton AcrylicHelper instance 获取 AcrylicHelper 单例"""
    global _acrylic_helper
    if _acrylic_helper is None:
        _acrylic_helper = AcrylicHelper()
    return _acrylic_helper
