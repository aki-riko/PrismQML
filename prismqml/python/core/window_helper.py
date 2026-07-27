# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""WindowHelper native operations exposed to QML. 暴露给 QML 的原生窗口操作。"""
import sys
import time
from typing import Any, Optional

from PySide6.QtCore import QObject, QPoint, QSize, Slot
from PySide6.QtGui import QGuiApplication, QIcon, QPainter, QPixmap, Qt

from ._folder_drop import FolderDropPathHelper
from ._icon_path import resolve_icon_path
from ._popup_owner import clear_popup_window_owner, ensure_popup_window_owner
from ._window_follower import (
    WINDOW_EDGE_BOTTOM,
    WINDOW_EDGE_LEFT,
    WINDOW_EDGE_RIGHT,
    WINDOW_EDGE_TOP,
    _MA_NOACTIVATE,
    _MINIMUM_NATIVE_EXTENT,
    _SWP_NOOWNERZORDER,
    _SWP_NOZORDER,
    _WINDOW_EDGES,
    _WM_MOUSEACTIVATE,
    _WindowFollowerFilter,
    _follower_rect,
    _follower_rect_for_extent,
    _set_qt_follower_geometry,
    _window_device_pixel_ratio,
)
from .logger import warning, error, debug, exception


# SVG 渲染的多尺寸列表（用于生成高质量任务栏图标）
_ICON_SIZES = [16, 24, 32, 48, 64, 128, 256]

class WindowHelper(FolderDropPathHelper):
    """
    窗口辅助工具单例

    QML 中通过 WindowHelper.setAppIcon(iconPath) 调用。
    In QML: WindowHelper.setAppIcon(iconPath)
    """

    _instance: Optional["WindowHelper"] = None

    def __new__(cls, parent: Optional[QObject] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, parent: Optional[QObject] = None):
        if self._initialized:
            return
        super().__init__(parent)
        self._follower_filter: Optional[_WindowFollowerFilter] = None
        self._initialized = True

    def _ensure_follower_filter(self) -> Optional[_WindowFollowerFilter]:
        """Install the process native follower filter once. 安装一次进程级跟随过滤器。"""
        if sys.platform != "win32":
            return None
        if self._follower_filter is not None:
            return self._follower_filter
        app = QGuiApplication.instance()
        if app is None:
            warning("QGuiApplication 未创建，无法注册窗口跟随")
            return None
        try:
            candidate = _WindowFollowerFilter()
            app.installNativeEventFilter(candidate)
        except Exception as exc:
            exception(
                "Window follower filter installation failed: "
                f"{type(exc).__name__}: {exc}"
            )
            return None
        self._follower_filter = candidate
        return candidate

    @staticmethod
    def _window_id(window: Any) -> int:
        """Resolve a QWindow-compatible object to HWND. 将兼容 QWindow 的对象解析为 HWND。"""
        if window is None:
            return 0
        return int(window.winId())

    @Slot("QVariant", "QVariant", int, float, result=bool)
    def registerWindowFollower(
        self,
        host_window,
        follower_window,
        edge: int,
        logical_extent: float,
    ) -> bool:
        """Follow a host edge during native move/size loops. 在原生移动/缩放循环跟随宿主边缘。"""
        try:
            host_hwnd = self._window_id(host_window)
            follower_hwnd = self._window_id(follower_window)
            if (
                not host_hwnd
                or not follower_hwnd
                or edge not in _WINDOW_EDGES
                or logical_extent <= 0
            ):
                return False
            event_filter = self._ensure_follower_filter()
            scale = _window_device_pixel_ratio(host_window)
            physical_extent = max(
                _MINIMUM_NATIVE_EXTENT,
                round(logical_extent * scale),
            )
            return bool(
                event_filter
                and event_filter.register(
                    host_hwnd,
                    follower_hwnd,
                    edge,
                    physical_extent,
                )
            )
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            error(f"窗口跟随注册失败: {exc}")
            return False

    @Slot("QVariant", "QVariant", result=bool)
    def ensurePopupWindowOwner(self, popup_window, owner_window) -> bool:
        """Keep a Qt popup natively owned and above its host. 保持 Qt 弹层原生隶属并位于宿主上方。"""
        try:
            popup_flags = popup_window.flags() if popup_window else Qt.WindowType.Widget
            if (
                popup_flags & Qt.WindowType.WindowType_Mask
            ) != Qt.WindowType.Popup:
                return False
            popup_hwnd = self._window_id(popup_window)
            owner_hwnd = self._window_id(owner_window)
            return ensure_popup_window_owner(popup_hwnd, owner_hwnd)
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError) as exc:
            error(f"弹层原生 owner 修复失败: {exc}")
            return False

    @Slot("QVariant", "QVariant", result=bool)
    def clearPopupWindowOwner(self, popup_window, owner_window) -> bool:
        """Release a matching native popup owner. 解除匹配的原生弹层 owner。"""
        try:
            popup_flags = popup_window.flags() if popup_window else Qt.WindowType.Widget
            if (
                popup_flags & Qt.WindowType.WindowType_Mask
            ) != Qt.WindowType.Popup:
                return False
            popup_hwnd = self._window_id(popup_window)
            owner_hwnd = self._window_id(owner_window)
            return clear_popup_window_owner(popup_hwnd, owner_hwnd)
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError) as exc:
            error(f"弹层原生 owner 清理失败: {exc}")
            return False

    @Slot("QVariant", "QVariant", int, float, result=bool)
    def updateWindowFollowerGeometry(
        self,
        host_window,
        follower_window,
        edge: int,
        logical_extent: float,
    ) -> bool:
        """Submit one atomic outside-drawer frame. 原子提交一帧外侧抽屉几何。"""
        if edge not in _WINDOW_EDGES or logical_extent <= 0:
            return False
        try:
            if self._update_native_follower_geometry(
                host_window,
                follower_window,
                edge,
                logical_extent,
            ):
                return True
            return _set_qt_follower_geometry(
                host_window,
                follower_window,
                edge,
                logical_extent,
            )
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            error(f"窗口跟随几何更新失败: {exc}")
            return False

    def _update_native_follower_geometry(
        self,
        host_window,
        follower_window,
        edge: int,
        logical_extent: float,
    ) -> bool:
        """Try one native complete-RECT update. 尝试一次原生完整 RECT 更新。"""
        host_hwnd = self._window_id(host_window)
        follower_hwnd = self._window_id(follower_window)
        event_filter = self._ensure_follower_filter()
        physical_extent = max(
            _MINIMUM_NATIVE_EXTENT,
            round(logical_extent * _window_device_pixel_ratio(host_window)),
        )
        return bool(
            host_hwnd
            and follower_hwnd
            and event_filter
            and event_filter.update_geometry(
                host_hwnd,
                follower_hwnd,
                edge,
                physical_extent,
            )
        )

    @Slot("QVariant", result=bool)
    def unregisterWindowFollower(self, follower_window) -> bool:
        """Remove one native follower binding. 移除一个原生附属窗口绑定。"""
        try:
            follower_hwnd = self._window_id(follower_window)
            if not follower_hwnd or self._follower_filter is None:
                return False
            return self._follower_filter.unregister(follower_hwnd)
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            error(f"窗口跟随解绑失败: {exc}")
            return False

    @Slot(str)
    def setAppIcon(self, icon: str) -> None:
        """Set taskbar icon from local/file/qrc paths. 从本地或资源路径设置图标。"""
        if not icon:
            return
        profile_start = time.perf_counter()
        icon_path = self._resolveIconPath(icon)
        resolve_ms = int((time.perf_counter() - profile_start) * 1000)
        if not icon_path:
            warning(f"无法解析图标路径: {icon}")
            return
        app = QGuiApplication.instance()
        if not app:
            warning("QGuiApplication 未创建，无法设置图标")
            return
        if self._try_set_svg_icon(app, icon_path, profile_start, resolve_ms):
            return
        self._set_bitmap_icon(app, icon_path, profile_start, resolve_ms)

    @Slot(int, int, result="QVariantMap")
    def availableScreenGeometryAt(self, x: int, y: int) -> dict[str, int]:
        """Return the available geometry for the screen containing a global point."""
        app = QGuiApplication.instance()
        if app is None:
            return {}
        screen = app.screenAt(QPoint(x, y))
        if screen is None:
            screen = app.primaryScreen()
        if screen is None:
            return {}
        geometry = screen.availableGeometry()
        return {
            "x": geometry.x(),
            "y": geometry.y(),
            "width": geometry.width(),
            "height": geometry.height(),
        }

    def _try_set_svg_icon(
        self,
        app: QGuiApplication,
        icon_path: str,
        profile_start: float,
        resolve_ms: int,
    ) -> bool:
        """Render and publish an SVG when applicable. 按需渲染并发布 SVG。"""
        if not icon_path.lower().endswith(".svg"):
            return False
        render_start = time.perf_counter()
        qicon = self._renderSvgIcon(icon_path)
        if not qicon or qicon.isNull():
            return False
        app.setWindowIcon(qicon)
        debug(
            "[启动剖析] WindowHelper.setAppIcon SVG: "
            f"resolve={resolve_ms}ms / "
            f"render={int((time.perf_counter() - render_start) * 1000)}ms / "
            f"total={int((time.perf_counter() - profile_start) * 1000)}ms"
        )
        debug(f"任务栏图标已设置 (SVG): {icon_path}")
        return True

    @staticmethod
    def _set_bitmap_icon(
        app: QGuiApplication,
        icon_path: str,
        profile_start: float,
        resolve_ms: int,
    ) -> None:
        """Load and publish a bitmap icon. 加载并发布位图图标。"""
        qicon = QIcon(icon_path)
        if qicon.isNull():
            warning(f"图标加载失败: {icon_path}")
            return
        app.setWindowIcon(qicon)
        debug(
            "[启动剖析] WindowHelper.setAppIcon bitmap: "
            f"resolve={resolve_ms}ms / "
            f"total={int((time.perf_counter() - profile_start) * 1000)}ms"
        )
        debug(f"任务栏图标已设置: {icon_path}")

    @staticmethod
    def _resolveIconPath(icon: str) -> str:
        """解析各类图标路径为可用的文件路径

        Args:
            icon: 原始图标路径

        Returns:
            解析后的文件路径
        """
        return resolve_icon_path(icon)

    @staticmethod
    def _renderSvgIcon(svg_path: str) -> Optional[QIcon]:
        """Render one SVG into a multi-size icon. 将 SVG 渲染为多尺寸图标。"""
        try:
            from PySide6.QtSvg import QSvgRenderer

            renderer = QSvgRenderer(svg_path)
            if not renderer.isValid():
                warning(f"SVG 渲染器无效: {svg_path}")
                return None
            return WindowHelper._render_svg_sizes(renderer)
        except ImportError:
            warning("PySide6.QtSvg 未安装，SVG 图标无法渲染")
            return None
        except Exception as e:
            error(f"SVG 图标渲染失败: {e}")
            return None

    @staticmethod
    def _render_svg_sizes(renderer) -> QIcon:
        """Render all taskbar sizes. 渲染全部任务栏尺寸。"""
        qicon = QIcon()
        for size in _ICON_SIZES:
            pixmap = QPixmap(QSize(size, size))
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            qicon.addPixmap(pixmap)
        return qicon


def get_window_helper() -> WindowHelper:
    """获取 WindowHelper 单例"""
    return WindowHelper()
