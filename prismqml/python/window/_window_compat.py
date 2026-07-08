# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Window compatibility API mixin 窗口兼容 API Mixin"""

from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtQuick import QQuickItem, QQuickWindow

from ..core.logger import debug


class WindowCompatMixin:
    """QWidget-compatible window operations for WindowCore."""

    def _restore_visible_state(self):
        if not self._window:
            return

        try:
            from PySide6.QtCore import QMetaObject

            QMetaObject.invokeMethod(self._window, "restoreVisibleState")
        except Exception as e:
            debug(f"restoreVisibleState invoke failed: {e}")

        try:
            self._window.setOpacity(1.0)
            self._window.setProperty("opacity", 1.0)
            self._window.setProperty("_animOpacity", 1.0)
            self._window.setProperty("_animScale", 1.0)
            self._window.update()
        except Exception as e:
            debug(f"visible state fallback failed: {e}")

    def hide(self):
        if self._window:
            self._window.hide()

    def isVisible(self) -> bool:
        """转发到 QQuickWindow.isVisible — Resource monitor 和外部代码常用 isVisible 检查
        窗口是否可见; 提供给跟 QWidget 行为对齐的代码使用"""
        return bool(self._window and self._window.isVisible())

    def activateWindow(self):
        """转发到 QQuickWindow.requestActivate — 跟 QWidget API 对齐;
        托盘点击 / 外部唤起主窗口时把窗口提到前台并获得焦点"""
        if self._window:
            self._window.requestActivate()

    def showNormal(self):
        """转发到 QQuickWindow.showNormal — 跟 QWidget API 对齐;
        从最小化/最大化恢复为普通窗口状态"""
        if self._window:
            self._restore_visible_state()
            self._window.showNormal()
            self._restore_visible_state()

    def showMinimized(self):
        """转发到 QQuickWindow.showMinimized — 跟 QWidget API 对齐"""
        if self._window:
            self._window.showMinimized()

    def showMaximized(self):
        """转发到 QQuickWindow.showMaximized — 跟 QWidget API 对齐"""
        if self._window:
            self._restore_visible_state()
            self._window.showMaximized()
            self._restore_visible_state()

    def isMaximized(self) -> bool:
        """通过 QQuickWindow.visibility 判定 — 跟 QWidget API 对齐;
        QWindow.Visibility.Maximized 对应最大化状态"""
        if not self._window:
            return False
        return self._window.visibility() == QQuickWindow.Visibility.Maximized

    def isMinimized(self) -> bool:
        """通过 QQuickWindow.visibility 判定 — 跟 QWidget API 对齐"""
        if not self._window:
            return False
        return self._window.visibility() == QQuickWindow.Visibility.Minimized

    def raise_(self):
        """转发到 QQuickWindow.raise_ — 跟 QWidget API 对齐;
        把窗口提升到同级窗口栈最前"""
        if self._window:
            self._window.raise_()

    def windowFlags(self):
        """转发到 QWindow.flags — 跟 QWidget API 对齐"""
        if not self._window:
            return Qt.WindowFlags()
        return self._window.flags()

    def setWindowFlags(self, flags):
        """转发到 QWindow.setFlags — 跟 QWidget API 对齐;
        QWidget 改 flags 后需要 show() 重新生效,QWindow.setFlags 行为一致"""
        if self._window:
            self._window.setFlags(flags)

    def setMinimumSize(self, width: int, height: int):
        """转发到 QWindow.setMinimumSize — 跟 QWidget API 对齐;
        Initialization manager / 主窗口构造期会调,QWindow 未创建时缓存到字面量,
        _create_window 拼 QML 时读 self._min_width/_min_height"""
        from PySide6.QtCore import QSize

        self._min_width = width
        self._min_height = height
        if self._window:
            self._window.setMinimumSize(QSize(width, height))

    def setMaximumSize(self, width: int, height: int):
        """转发到 QWindow.setMaximumSize — 跟 QWidget API 对齐"""
        from PySide6.QtCore import QSize

        self._max_width = width
        self._max_height = height
        if self._window:
            self._window.setMaximumSize(QSize(width, height))

    def repaint(self):
        """转发到 QQuickWindow.update — 跟 QWidget API 对齐;
        QWidget.repaint 是同步立即重绘,QQuickWindow 没有同步 API,
        update() 是请求下一帧重绘 — 休眠唤醒 / power monitor 触发用足够"""
        if self._window:
            self._window.update()

    def closeEvent(self, event: "WindowCloseEvent"):
        """Handle a QML/native close request.

        Subclasses may call event.ignore() to cancel the close. The default
        mirrors QWidget behavior and accepts the request.
        """
        event.accept()

    def close(self):
        if self._window:
            result = self._window.close()
            closed = result is not False
            if closed:
                self.windowClosed.emit()
            return closed
        return False

    def addOverlay(self, widget: Any):
        """添加覆盖层组件（如Drawer、Dialog等）到窗口层级

        Args:
            widget: 要添加的覆盖层组件

        Note:
            覆盖层组件会被添加到窗口的contentItem，覆盖所有内容。
            适用于Drawer、MessageBox、Dialog等需要全屏覆盖的组件。
        """
        if self._window and hasattr(widget, "_qml_item") and widget._qml_item:
            widget._qml_item.setParentItem(self._window.contentItem())

    def getContentItem(self) -> Optional[QQuickItem]:
        """获取窗口的contentContainer，用于添加覆盖层组件"""
        if self._window:
            # 查找contentContainer（WindowCore中定义的内容区域）
            content_container = self._window.findChild(QQuickItem, "contentContainer")
            if content_container:
                return content_container
            # 回退到contentItem
            return self._window.contentItem()
        return None
