# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是FluentQML的一部分，采用MIT许可证授权。
"""
FluentQML SystemTray - 系统托盘组件

功能：
- 系统托盘图标管理
- 与QML菜单集成
- 支持气泡消息
- 左键 / 右键弹出菜单
- aboutToShow 信号（弹出前动态刷新）
- 可勾选项、禁用项、子菜单、单项更新/删除
"""

from typing import Union, Optional, Callable, List
from enum import Enum

from PySide6.QtCore import QObject, Signal, Slot, Property, QUrl, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon, QCursor
from PySide6.QtWidgets import QSystemTrayIcon
from PySide6.QtQml import QQmlComponent

from ..core.logger import info, warning, error
from ..core.icons import Icon
from ..core.engine import EngineManager
from ..core.utils import qml_path


from .tray_types import MessageIcon, ActivationReason


class SystemTrayIcon(QObject):
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
        tray.setToolTip("FluentQML App")

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
            self._tray.setIcon(QIcon(icon))
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

    # ==================== Menu Methods 菜单方法 ====================

    def _ensureQmlMenu(self):
        """确保QML菜单已创建 Ensure QML menu is created"""
        if self._qml_menu is not None:
            return

        try:
            engine = EngineManager.get_engine()
            qml_dir = qml_path()
            menu_path = qml_dir / "controls" / "menus" / "SystemTrayMenu.qml"

            # 保持component引用防止被GC
            self._component = QQmlComponent(engine, QUrl.fromLocalFile(str(menu_path)))
            if self._component.isError():
                errors = "\n".join([e.toString() for e in self._component.errors()])
                error(f"Failed to load SystemTrayMenu: {errors}")
                return

            self._qml_menu = self._component.create()
            if self._qml_menu is None:
                error("Failed to create SystemTrayMenu instance")
                return

            # 设置parent防止被GC
            self._qml_menu.setParent(self)

            # 连接菜单的actionTriggered信号
            self._qml_menu.actionTriggered.connect(self._onMenuActionTriggered)

            # 添加已存储的actions
            for action in self._actions:
                self._addActionToQml(action)

        except RuntimeError as e:
            warning(f"QML engine not ready: {e}")

    def _addActionToQml(self, action: dict):
        """添加action到QML菜单"""
        if self._qml_menu is None:
            return

        if action.get("separator"):
            QMetaObject.invokeMethod(self._qml_menu, "addSeparator")
            return

        text = action.get("text", "")
        icon = action.get("icon", "")
        shortcut = action.get("shortcut", "")

        # 转换Icon枚举为字符串
        if isinstance(icon, Icon):
            icon = icon.value
        elif isinstance(icon, QIcon):
            icon = ""  # QML菜单暂不支持QIcon

        # 构建 options 对象
        options = {}
        if action.get("actionId"):
            options["actionId"] = action["actionId"]
        if action.get("checkable") is not None:
            options["checkable"] = action["checkable"]
        if action.get("checked") is not None:
            options["checked"] = action["checked"]
        if action.get("enabled") is not None:
            options["enabled"] = action["enabled"]
        if action.get("toolTip"):
            options["toolTip"] = action["toolTip"]
        if action.get("hasSubmenu"):
            options["hasSubmenu"] = action["hasSubmenu"]

        # 调用 QML addAction(text, icon, shortcut, options)
        QMetaObject.invokeMethod(
            self._qml_menu,
            "addAction",
            Q_ARG("QVariant", text),
            Q_ARG("QVariant", icon),
            Q_ARG("QVariant", shortcut),
            Q_ARG("QVariant", options),
        )

    @Slot(str)
    def _onMenuActionTriggered(self, actionIdOrText: str):
        """处理菜单项点击"""
        if actionIdOrText in self._callbacks:
            callback = self._callbacks[actionIdOrText]
            if callback:
                callback()

    def addAction(
        self,
        text: str,
        icon: Union[Icon, str, None] = None,
        shortcut: str = "",
        triggered: Optional[Callable] = None,
        actionId: str = "",
        checkable: bool = False,
        checked: bool = False,
        enabled: bool = True,
        toolTip: str = "",
    ):
        """
        添加菜单动作 Add menu action

        Args:
            text: 动作文本
            icon: 图标（Icon枚举或图标名称字符串）
            shortcut: 快捷键
            triggered: 触发回调
            actionId: 唯一标识符（用于后续更新/删除）
            checkable: 是否可勾选
            checked: 是否已勾选（仅 checkable=True 时有效）
            enabled: 是否启用（False 则灰显不可点击）
            toolTip: 悬停提示文本

        Example:
            tray.addAction("显示主窗口", Icon.HOME, triggered=window.show)
            tray.addAction("退出", Icon.POWER, triggered=app.quit)
            tray.addAction("静音", checkable=True, checked=False, actionId="mute")
        """
        action = {
            "text": text,
            "icon": icon,
            "shortcut": shortcut,
            "actionId": actionId or text,
            "checkable": checkable,
            "checked": checked,
            "enabled": enabled,
            "toolTip": toolTip,
        }
        # 检查 actionId 重复（不包括分隔线）
        final_id = action["actionId"]
        for existing in self._actions:
            if existing.get("actionId") == final_id:
                warning(f"SystemTrayIcon: duplicate actionId '{final_id}', "
                        "updateAction/removeAction 可能操作错误项")
                break
        self._actions.append(action)

        # 注册回调（用 actionId 优先，fallback 到 text）
        callback_key = actionId or text
        if triggered:
            self._callbacks[callback_key] = triggered

        # 如果QML菜单已创建，直接添加
        if self._qml_menu:
            self._addActionToQml(action)

    def addActions(self, actions: List[dict]):
        """
        批量添加菜单动作 Add multiple menu actions

        Args:
            actions: 动作列表，格式 [{"text": "...", "icon": ..., "triggered": ..., ...}, ...]
        """
        for a in actions:
            self.addAction(
                text=a.get("text", ""),
                icon=a.get("icon"),
                shortcut=a.get("shortcut", ""),
                triggered=a.get("triggered"),
                actionId=a.get("actionId", ""),
                checkable=a.get("checkable", False),
                checked=a.get("checked", False),
                enabled=a.get("enabled", True),
                toolTip=a.get("toolTip", ""),
            )

    def addSeparator(self):
        """添加分隔线 Add separator"""
        self._actions.append({"separator": True})
        if self._qml_menu:
            QMetaObject.invokeMethod(self._qml_menu, "addSeparator")

    def clearActions(self):
        """清空所有菜单动作 Clear all menu actions"""
        self._actions.clear()
        self._callbacks.clear()
        if self._qml_menu:
            QMetaObject.invokeMethod(self._qml_menu, "clear")

    def actions(self) -> List[dict]:
        """获取所有菜单动作配置 Get all menu action configs"""
        return self._actions.copy()

    # ==================== Single Item Operations 单项操作 ====================

    def updateAction(self, actionId: str, **props):
        """
        按 ID 更新单个菜单项的属性 Update a single action's properties by ID

        Args:
            actionId: 动作标识符
            **props: 要更新的属性 (text, icon, checkable, checked, enabled, toolTip, shortcut)

        Example:
            tray.updateAction("mute", checked=True, text="取消静音")
        """
        # 更新本地存储
        for action in self._actions:
            if action.get("actionId") == actionId:
                action.update(props)
                break

        # 更新回调
        if "triggered" in props:
            self._callbacks[actionId] = props.pop("triggered")

        # 更新 QML 侧
        if self._qml_menu and props:
            QMetaObject.invokeMethod(
                self._qml_menu,
                "updateAction",
                Q_ARG("QVariant", actionId),
                Q_ARG("QVariant", props),
            )

    def removeAction(self, actionId: str):
        """
        按 ID 删除单个菜单项 Remove a single action by ID

        Args:
            actionId: 动作标识符
        """
        self._actions = [a for a in self._actions if a.get("actionId") != actionId]
        self._callbacks.pop(actionId, None)

        if self._qml_menu:
            QMetaObject.invokeMethod(
                self._qml_menu, "removeAction", Q_ARG("QVariant", actionId)
            )

    def setActionChecked(self, actionId: str, checked: bool):
        """
        设置菜单项的勾选状态 Set action's checked state

        Args:
            actionId: 动作标识符
            checked: 是否勾选
        """
        self.updateAction(actionId, checked=checked)

    def setActionEnabled(self, actionId: str, enabled: bool):
        """
        设置菜单项的启用状态 Set action's enabled state

        Args:
            actionId: 动作标识符
            enabled: 是否启用
        """
        self.updateAction(actionId, enabled=enabled)

    def setActionText(self, actionId: str, text: str):
        """
        设置菜单项的文本 Set action's text

        Args:
            actionId: 动作标识符
            text: 新文本
        """
        self.updateAction(actionId, text=text)

    # ==================== Submenu 子菜单 ====================

    def addMenu(
        self,
        text: str,
        icon: Union[Icon, str, None] = None,
        actions: Optional[List[dict]] = None,
    ):
        """
        添加子菜单 Add submenu

        Args:
            text: 子菜单父项文本
            icon: 图标
            actions: 子菜单的动作列表

        Note:
            子菜单中的动作 triggered 回调通过 actionId 注册。

        Example:
            tray.addMenu("盘符", icon=Icon.FOLDER, actions=[
                {"text": "NAS (Z:)", "actionId": "drive_Z", "triggered": lambda: open_drive("Z")},
                {"text": "OneDrive (Y:)", "actionId": "drive_Y", "triggered": lambda: open_drive("Y")},
            ])
        """
        action = {
            "text": text,
            "icon": icon,
            "hasSubmenu": True,
            "actionId": f"_submenu_{text}",
            "submenuActions": actions or [],
        }
        self._actions.append(action)

        # 注册子菜单中每个动作的回调
        if actions:
            for sub_action in actions:
                sub_id = sub_action.get("actionId", sub_action.get("text", ""))
                if sub_action.get("triggered"):
                    self._callbacks[sub_id] = sub_action["triggered"]

        if self._qml_menu:
            self._addActionToQml(action)

    # ==================== Message Methods 消息方法 ====================

    def showMessage(
        self,
        title: str,
        message: str,
        icon: MessageIcon = MessageIcon.Information,
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
        self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon(icon.value), msecs)

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
    """
    创建系统托盘图标 Create system tray icon

    便捷函数，一步创建并配置系统托盘图标。

    Args:
        icon: 托盘图标
        parent: 父对象
        toolTip: 鼠标悬停提示
        actions: 菜单动作列表
        menuOnLeftClick: 左键是否弹菜单

    Returns:
        SystemTrayIcon实例

    Example:
        ```python
        tray = createSystemTrayIcon(
            icon=Icon.HOME,
            parent=window,
            toolTip="My App",
            actions=[
                {"text": "显示", "icon": Icon.HOME, "triggered": window.show},
                {"text": "退出", "icon": Icon.POWER, "triggered": app.quit},
            ]
        )
        tray.show()
        ```
    """
    tray = SystemTrayIcon(
        icon=icon, parent=parent, toolTip=toolTip, menuOnLeftClick=menuOnLeftClick
    )

    if actions:
        tray.addActions(actions)

    return tray
