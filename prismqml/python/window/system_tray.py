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

from typing import Union, Optional, Callable, List
from enum import Enum

from PySide6.QtCore import QObject, Signal, Slot, Property, QUrl, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon, QCursor
from PySide6.QtWidgets import QSystemTrayIcon
from PySide6.QtQml import QQmlComponent

from ..core.logger import info, warning, error
from ..core.icons import Icon
from ..core._icon_path import resolve_icon_path
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

    # ==================== Menu Methods 菜单方法 ====================

    def _ensureQmlMenu(self):
        """确保QML菜单已创建 Ensure QML menu is created"""
        if self._qml_menu is not None:
            return
        try:
            self._create_qml_menu(EngineManager.get_engine())
        except RuntimeError as e:
            warning(f"QML engine not ready: {e}")

    def _create_qml_menu(self, engine) -> None:
        """Create and populate the QML menu. 创建并填充 QML 菜单。"""
        menu_path = qml_path() / "controls" / "menus" / "SystemTrayMenu.qml"
        self._component = QQmlComponent(engine, QUrl.fromLocalFile(str(menu_path)))
        if self._component.isError():
            errors = "\n".join(error.toString() for error in self._component.errors())
            error(f"Failed to load SystemTrayMenu: {errors}")
            return
        self._qml_menu = self._component.create()
        if self._qml_menu is None:
            error("Failed to create SystemTrayMenu instance")
            return
        self._qml_menu.setParent(self)
        self._qml_menu.actionTriggered.connect(self._onMenuActionTriggered)
        for action in self._actions:
            self._addActionToQml(action)

    @staticmethod
    def _qml_icon_value(icon):
        """Convert one Python icon into QML data. 转换 Python 图标为 QML 数据。"""
        if isinstance(icon, Icon):
            return icon.value
        if isinstance(icon, QIcon):
            return ""
        return icon or ""

    @staticmethod
    def _action_options(action: dict) -> dict:
        """Build public QML action options. 构造公开 QML 动作选项。"""
        keys = ("actionId", "checkable", "checked", "enabled", "toolTip", "hasSubmenu")
        return {
            key: action[key]
            for key in keys
            if action.get(key) is not None and action.get(key) != ""
        }

    def _submenu_payload(self, action: dict) -> List[dict]:
        """Serialize submenu actions without Python callbacks. 序列化子菜单动作。"""
        payload = []
        for sub_action in action.get("submenuActions", []):
            item = {key: value for key, value in sub_action.items() if key != "triggered"}
            item["actionId"] = item.get("actionId") or item.get("text", "")
            item["icon"] = self._qml_icon_value(item.get("icon"))
            payload.append(item)
        return payload

    def _addActionToQml(self, action: dict):
        """添加action到QML菜单"""
        if self._qml_menu is None:
            return
        if action.get("separator"):
            QMetaObject.invokeMethod(self._qml_menu, "addSeparator")
            return
        text = action.get("text", "")
        icon = self._qml_icon_value(action.get("icon"))
        if action.get("hasSubmenu"):
            QMetaObject.invokeMethod(
                self._qml_menu,
                "addSubmenuActions",
                Q_ARG("QVariant", text),
                Q_ARG("QVariant", icon),
                Q_ARG("QVariant", self._submenu_payload(action)),
            )
            return
        shortcut = action.get("shortcut", "")
        QMetaObject.invokeMethod(
            self._qml_menu,
            "addAction",
            Q_ARG("QVariant", text),
            Q_ARG("QVariant", icon),
            Q_ARG("QVariant", shortcut),
            Q_ARG("QVariant", self._action_options(action)),
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
        """Add one menu action and callback. 添加单个菜单动作与回调。"""
        action = self._build_action(
            text, icon, shortcut, actionId, checkable, checked, enabled, toolTip
        )
        self._warn_duplicate_action_id(action["actionId"])
        self._actions.append(action)
        if triggered:
            self._callbacks[action["actionId"]] = triggered
        if self._qml_menu:
            self._addActionToQml(action)

    @staticmethod
    def _build_action(
        text, icon, shortcut, action_id, checkable, checked, enabled, tool_tip
    ) -> dict:
        """Build normalized action storage. 构造规范化动作存储。"""
        return {
            "text": text,
            "icon": icon,
            "shortcut": shortcut,
            "actionId": action_id or text,
            "checkable": checkable,
            "checked": checked,
            "enabled": enabled,
            "toolTip": tool_tip,
        }

    def _warn_duplicate_action_id(self, action_id: str) -> None:
        """Warn when item mutation would be ambiguous. 警告会导致单项操作歧义的重复 ID。"""
        for existing in self._actions:
            if existing.get("actionId") != action_id:
                continue
            warning(
                f"SystemTrayIcon: duplicate actionId '{action_id}', "
                "updateAction/removeAction 可能操作错误项"
            )
            return

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
        """Add a data-backed submenu. 添加数据驱动子菜单。"""
        submenu_actions = actions or []
        action = {
            "text": text,
            "icon": icon,
            "hasSubmenu": True,
            "actionId": f"_submenu_{text}",
            "submenuActions": submenu_actions,
        }
        self._actions.append(action)
        self._register_submenu_callbacks(submenu_actions)
        if self._qml_menu:
            self._addActionToQml(action)

    def _register_submenu_callbacks(self, actions: List[dict]) -> None:
        """Register callbacks for submenu action IDs. 注册子菜单动作回调。"""
        for action in actions:
            callback = action.get("triggered")
            if not callback:
                continue
            action_id = action.get("actionId") or action.get("text", "")
            self._callbacks[action_id] = callback

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
