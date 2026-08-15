# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""
PrismQML SystemTray - 系统托盘组件

功能：
- 系统托盘图标管理
- 与QML菜单集成
- 支持气泡消息
- 左键 / 右键弹出菜单
- aboutToShow 信号（弹出前动态刷新）
- 可勾选项、禁用项、子菜单、单项更新/删除
"""

from typing import Union, Optional, List
from PySide6.QtCore import (
    QObject,
    Signal,
    Property,
    QMetaObject,
    Q_ARG,
)
from PySide6.QtGui import QIcon, QCursor
from PySide6.QtWidgets import QSystemTrayIcon

from ..core.icons import Icon
from ..core._icon_path import resolve_icon_path


from .tray_types import MessageIcon
from ._system_tray_menu import SystemTrayMenuMixin


class SystemTrayIcon(SystemTrayMenuMixin, QObject):
    """
    系统托盘图标 System tray icon

    封装QSystemTrayIcon，提供更友好的API和与QML菜单的集成。

    Args:
        icon: 托盘图标
        parent: 父对象（通常是主窗口）
        toolTip: 鼠标悬停提示
        menuOnLeftClick: 左键是否也弹出菜单（默认 True）

    Signals:
        activated: 托盘图标被激活（点击等）
        messageClicked: 气泡消息被点击
        aboutToShow: 菜单即将显示（在此回调中刷新菜单内容）

    Example:
        ```python
        from prismqml import SystemTrayIcon

        tray = SystemTrayIcon(icon=window.windowIcon(), parent=window)
        tray.setToolTip("PrismQML App")

        # 动态菜单
        tray.aboutToShow.connect(rebuild_menu)

        # 添加菜单项
        tray.addAction("显示", triggered=window.show)
        tray.addSeparator()
        tray.addAction("退出", triggered=app.quit)

        tray.show()
        ```
    """

    # ==================== Signals 信号 ====================
    activated = Signal(int)  # ActivationReason
    messageClicked = Signal()
    aboutToShow = Signal()  # Emitted before menu is shown 菜单显示前发射

    def __init__(
        self,
        icon: Union[QIcon, Icon, str, None] = None,
        parent: Optional[QObject] = None,
        toolTip: str = "",
        menuOnLeftClick: bool = True,
    ):
        super().__init__(parent)

        self._tray = QSystemTrayIcon(parent)
        self._qml_menu = None  # QML SystemTrayMenu 实例
        self._actions: List[dict] = []  # 存储 action 配置
        self._callbacks: dict = {}  # text/actionId -> callback
        self._parent = parent
        self._menu_on_left_click = menuOnLeftClick

        # 设置图标 Set icon
        if icon:
            self.setIcon(icon)
        elif parent and hasattr(parent, "windowIcon"):
            self.setIcon(parent.windowIcon())

        # 设置提示 Set tooltip
        if toolTip:
            self.setToolTip(toolTip)

        # 连接信号 Connect signals
        self._tray.activated.connect(self._onActivated)
        self._tray.messageClicked.connect(self.messageClicked.emit)

    # ==================== Icon Methods 图标方法 ====================

    def setIcon(self, icon: Union[QIcon, Icon, str]):
        """
        设置托盘图标 Set tray icon

        Args:
            icon: QIcon、Icon枚举或图片路径
        """
        if isinstance(icon, Icon):
            self._tray.setIcon(icon.to_qicon())
        elif isinstance(icon, str):
            self._tray.setIcon(QIcon(resolve_icon_path(icon)))
        else:
            self._tray.setIcon(icon)

    def icon(self) -> QIcon:
        """获取托盘图标 Get tray icon"""
        return self._tray.icon()

    # ==================== Tooltip Methods 提示方法 ====================

    def setToolTip(self, tip: str):
        """
        设置鼠标悬停提示 Set mouse hover tooltip

        Args:
            tip: 提示文本
        """
        self._tray.setToolTip(tip)

    def toolTip(self) -> str:
        """获取提示文本 Get tooltip text"""
        return self._tray.toolTip()

    # ==================== Visibility Methods 可见性方法 ====================

    def show(self):
        """显示托盘图标 Show tray icon"""
        self._tray.show()

    def hide(self):
        """隐藏托盘图标 Hide tray icon"""
        self._tray.hide()

    def setVisible(self, visible: bool):
        """
        设置可见性 Set visibility

        Args:
            visible: 是否可见
        """
        self._tray.setVisible(visible)

    def isVisible(self) -> bool:
        """是否可见 Is visible"""
        return self._tray.isVisible()

    # ==================== Message Methods 消息方法 ====================

    def showMessage(
        self,
        title: str,
        message: str,
        icon: Union[MessageIcon, QSystemTrayIcon.MessageIcon, int, None] = MessageIcon.Information,
        msecs: int = 5000,
    ):
        """
        显示气泡消息 Show balloon message

        Args:
            title: 消息标题
            message: 消息内容
            icon: 消息图标类型
            msecs: 显示时长（毫秒）
        """
        message_icon = self._coerceMessageIcon(icon)
        self._tray.showMessage(title, message, message_icon, msecs)

    def _coerceMessageIcon(
        self, icon: Union[MessageIcon, QSystemTrayIcon.MessageIcon, int, QIcon, None]
    ) -> QSystemTrayIcon.MessageIcon:
        if icon is None or isinstance(icon, QIcon):
            return QSystemTrayIcon.MessageIcon.Information
        if isinstance(icon, MessageIcon):
            return QSystemTrayIcon.MessageIcon(icon.value)
        if isinstance(icon, QSystemTrayIcon.MessageIcon):
            return icon
        try:
            return QSystemTrayIcon.MessageIcon(int(icon))
        except (TypeError, ValueError):
            return QSystemTrayIcon.MessageIcon.Information

    def showInfoMessage(self, title: str, message: str, msecs: int = 5000):
        """显示信息消息 Show info message"""
        self.showMessage(title, message, MessageIcon.Information, msecs)

    def showWarningMessage(self, title: str, message: str, msecs: int = 5000):
        """显示警告消息 Show warning message"""
        self.showMessage(title, message, MessageIcon.Warning, msecs)

    def showErrorMessage(self, title: str, message: str, msecs: int = 5000):
        """显示错误消息 Show error message"""
        self.showMessage(title, message, MessageIcon.Critical, msecs)

    # ==================== Static Methods 静态方法 ====================

    @staticmethod
    def isSystemTrayAvailable() -> bool:
        """检查系统托盘是否可用 Check if system tray is available"""
        return QSystemTrayIcon.isSystemTrayAvailable()

    @staticmethod
    def supportsMessages() -> bool:
        """检查是否支持气泡消息 Check if balloon messages are supported"""
        return QSystemTrayIcon.supportsMessages()

    # ==================== Internal Methods 内部方法 ====================

    def _onActivated(self, reason: QSystemTrayIcon.ActivationReason):
        """处理激活事件 Handle activation event"""
        should_show_menu = False

        # 右键总是弹菜单
        if reason == QSystemTrayIcon.ActivationReason.Context:
            should_show_menu = True

        # 左键根据配置决定
        if (
            reason == QSystemTrayIcon.ActivationReason.Trigger
            and self._menu_on_left_click
        ):
            should_show_menu = True

        if should_show_menu:
            # 发射 aboutToShow 信号，让调用方在此刷新菜单
            self.aboutToShow.emit()
            self._showQmlMenu()

        # 转换为int避免Shiboken警告
        self.activated.emit(reason.value)

    def _showQmlMenu(self):
        """显示QML菜单 Show QML menu"""
        self._ensureQmlMenu()
        if self._qml_menu is None:
            return

        # 获取光标位置
        pos = QCursor.pos()

        # 调用QML菜单的showAtPosition方法
        QMetaObject.invokeMethod(
            self._qml_menu,
            "showAtPosition",
            Q_ARG("QVariant", pos.x()),
            Q_ARG("QVariant", pos.y()),
        )

    # ==================== Properties for QML 供QML使用的属性 ====================

    @Property(bool, constant=True)
    def available(self) -> bool:
        """系统托盘是否可用 Is system tray available"""
        return self.isSystemTrayAvailable()


# ==================== Convenience Functions 便捷函数 ====================


def createSystemTrayIcon(
    icon: Union[QIcon, Icon, str, None] = None,
    parent: Optional[QObject] = None,
    toolTip: str = "",
    actions: Optional[List[dict]] = None,
    menuOnLeftClick: bool = True,
) -> SystemTrayIcon:
    """Create and configure one tray icon. 创建并配置单个托盘图标。"""
    tray = SystemTrayIcon(
        icon=icon, parent=parent, toolTip=toolTip, menuOnLeftClick=menuOnLeftClick
    )

    if actions:
        tray.addActions(actions)

    return tray
