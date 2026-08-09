# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""WindowHelper native operations exposed to QML. 暴露给 QML 的原生窗口操作。"""
import os
import sys
import time
from typing import Any, Optional

from PySide6.QtCore import QObject, QPoint, QResource, QUrl, Slot
from PySide6.QtGui import QGuiApplication, QIcon, Qt

from ._icon_path import resolve_icon_path
from ._popup_owner import (
    clear_popup_window_owner,
    ensure_popup_window_owner,
    release_stale_popup_capture,
)
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
    _WM_WINDOWPOSCHANGING,
    _WindowFollowerFilter,
    _follower_rect,
    _follower_rect_for_extent,
    _set_qt_follower_geometry,
    _window_device_pixel_ratio,
)
from .logger import warning, error, debug, exception


# SVG 渲染的多尺寸列表（用于生成高质量任务栏图标）
_ICON_SIZES = [16, 24, 32, 48, 64, 128, 256]


def _screen_geometry_at(x: int, y: int, available: bool) -> dict[str, int]:
    """Return one screen geometry map. 返回指定屏幕的几何映射。"""
    app = QGuiApplication.instance()
    if app is None:
        return {}
    screen = app.screenAt(QPoint(x, y))
    if screen is None:
        screen = app.primaryScreen()
    if screen is None:
        return {}
    geometry = screen.availableGeometry() if available else screen.geometry()
    return {
        "x": geometry.x(),
        "y": geometry.y(),
        "width": geometry.width(),
        "height": geometry.height(),
    }


class WindowHelper(QObject):
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
        self._cached_svg_icon_path = ""
        self._cached_svg_icon_signature: Optional[tuple[Any, ...]] = None
        self._cached_svg_icon: Optional[QIcon] = None
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

    @Slot("QVariant", "QVariant", result=bool)
    def releasePopupWindowCapture(self, popup_window, owner_window) -> bool:
        """Release an idle owner capture blocking popup input. 释放阻塞弹层输入的空闲宿主捕获。"""
        try:
            popup_flags = popup_window.flags() if popup_window else Qt.WindowType.Widget
            if (
                popup_flags & Qt.WindowType.WindowType_Mask
            ) != Qt.WindowType.Popup:
                return False
            popup_hwnd = self._window_id(popup_window)
            owner_hwnd = self._window_id(owner_window)
            return release_stale_popup_capture(popup_hwnd, owner_hwnd)
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError) as exc:
            error(f"弹层鼠标捕获释放失败: {exc}")
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

    @Slot(QUrl, result=str)
    def resolveDroppedFolderPath(self, folder_url: QUrl) -> str:
        """Resolve a dropped folder only when a drop occurs. 仅在真实拖放时解析文件夹。"""
        from ._folder_drop import resolve_dropped_folder_path

        return resolve_dropped_folder_path(folder_url)

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
        """Return available geometry at a global point. 返回全局点所在工作区。"""
        return _screen_geometry_at(x, y, available=True)

    @Slot(int, int, result="QVariantMap")
    def screenGeometryAt(self, x: int, y: int) -> dict[str, int]:
        """Return full geometry at a global point. 返回全局点所在完整屏幕。"""
        return _screen_geometry_at(x, y, available=False)

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
        signature = self._svg_icon_signature(icon_path)
        qicon = self._get_cached_svg_icon(icon_path, signature)
        cache_hit = qicon is not None
        if qicon is None:
            qicon = self._renderSvgIcon(icon_path)
        if not qicon or qicon.isNull():
            return False
        if not cache_hit:
            self._cache_svg_icon(icon_path, signature, qicon)
        app.setWindowIcon(qicon)
        self._log_svg_icon_profile(
            icon_path, profile_start, render_start, resolve_ms, cache_hit
        )
        return True

    def _get_cached_svg_icon(
        self,
        icon_path: str,
        signature: Optional[tuple[Any, ...]],
    ) -> Optional[QIcon]:
        """Return a valid cached icon for the same source. 返回同源有效缓存图标。"""
        if (
            signature is None
            or icon_path != self._cached_svg_icon_path
            or signature != self._cached_svg_icon_signature
        ):
            return None
        cached_icon = self._cached_svg_icon
        if cached_icon is None or cached_icon.isNull():
            return None
        return cached_icon

    def _cache_svg_icon(
        self,
        icon_path: str,
        signature: Optional[tuple[Any, ...]],
        icon: QIcon,
    ) -> None:
        """Cache one validated SVG icon when its source is stable. 缓存稳定源的有效图标。"""
        if signature is None:
            return
        self._cached_svg_icon_path = icon_path
        self._cached_svg_icon_signature = signature
        self._cached_svg_icon = icon

    @staticmethod
    def _log_svg_icon_profile(
        icon_path: str,
        profile_start: float,
        render_start: float,
        resolve_ms: int,
        cache_hit: bool,
    ) -> None:
        """Log one SVG publication profile. 记录一次 SVG 发布性能。"""
        debug(
            "[启动剖析] WindowHelper.setAppIcon SVG: "
            f"resolve={resolve_ms}ms / "
            f"render={int((time.perf_counter() - render_start) * 1000)}ms / "
            f"cached={cache_hit} / "
            f"total={int((time.perf_counter() - profile_start) * 1000)}ms"
        )
        debug(f"任务栏图标已设置 (SVG): {icon_path}")

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
    def _svg_icon_signature(icon_path: str) -> Optional[tuple[Any, ...]]:
        """Return a stable cache signature for one SVG source. 返回SVG缓存签名。"""
        if icon_path.startswith(":/"):
            resource = QResource(icon_path)
            if not resource.isValid() or not resource.isFile():
                return None
            return ("qrc", bytes(resource.data()))
        try:
            stat_result = os.stat(icon_path)
        except OSError:
            return None
        return (stat_result.st_mtime_ns, stat_result.st_size)

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
        """Create a lazy fixed-size SVG icon. 创建惰性固定尺寸 SVG 图标。"""
        try:
            from ._taskbar_svg_icon import create_taskbar_svg_icon

            qicon = create_taskbar_svg_icon(svg_path, _ICON_SIZES)
            if qicon is None:
                warning(f"SVG 渲染器无效: {svg_path}")
                return None
            return qicon
        except ImportError:
            warning("PySide6.QtSvg 未安装，SVG 图标无法渲染")
            return None
        except Exception as e:
            error(f"SVG 图标渲染失败: {e}")
            return None


def get_window_helper() -> WindowHelper:
    """获取 WindowHelper 单例"""
    return WindowHelper()
