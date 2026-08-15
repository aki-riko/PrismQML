# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""QML menu protocol for the system tray. 系统托盘 QML 菜单协议。"""

from typing import Callable, List, Optional, Union

from PySide6.QtCore import Q_ARG, QMetaObject, QUrl, Slot
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlComponent

from ..core.icons import Icon
from ..core.logger import error, warning
from ..core.utils import qml_path


class SystemTrayMenuMixin:
    """Own the tray QML menu and action data protocol. 托盘 QML 菜单协议 owner。"""

    def _ensureQmlMenu(self):
        """确保QML菜单已创建 Ensure QML menu is created"""
        if self._qml_menu is not None:
            return
        try:
            from ..runtime import get_published_qml_engine

            self._create_qml_menu(get_published_qml_engine())
        except RuntimeError as e:
            warning(f"QML engine not ready: {e}")

    def _create_qml_menu(self, engine) -> None:
        """Create and populate the QML menu. 创建并填充 QML 菜单。"""
        menu_path = qml_path() / "controls" / "menus" / "SystemTrayMenu.qml"
        self._component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(menu_path)),
            parent=engine,
        )
        from ..runtime import register_qml_engine_binding

        register_qml_engine_binding(engine, self)
        if self._component.isError():
            errors = "\n".join(error.toString() for error in self._component.errors())
            error(f"Failed to load SystemTrayMenu: {errors}")
            return
        self._qml_menu = self._component.create()
        if self._qml_menu is None:
            error("Failed to create SystemTrayMenu instance")
            return
        self._qml_menu.setParent(engine)
        self._qml_menu.actionTriggered.connect(self._onMenuActionTriggered)
        for action in self._actions:
            self._addActionToQml(action)

    def release_engine(self) -> None:
        """Close engine-owned QML surfaces and drop references. 关闭引擎所拥有的 QML 界面并清除引用。"""
        import shiboken6

        menu = self._qml_menu
        if menu is not None and shiboken6.isValid(menu):
            QMetaObject.invokeMethod(menu, "prepareForEngineRelease")
        self._qml_menu = None
        self._component = None

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
        """批量添加菜单动作 Add multiple menu actions"""
        for action in actions:
            self.addAction(
                text=action.get("text", ""),
                icon=action.get("icon"),
                shortcut=action.get("shortcut", ""),
                triggered=action.get("triggered"),
                actionId=action.get("actionId", ""),
                checkable=action.get("checkable", False),
                checked=action.get("checked", False),
                enabled=action.get("enabled", True),
                toolTip=action.get("toolTip", ""),
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

    def updateAction(self, actionId: str, **props):
        """按 ID 更新单个菜单项的属性 Update a single action's properties by ID"""
        for action in self._actions:
            if action.get("actionId") == actionId:
                action.update(props)
                break
        if "triggered" in props:
            self._callbacks[actionId] = props.pop("triggered")
        if self._qml_menu and props:
            QMetaObject.invokeMethod(
                self._qml_menu,
                "updateAction",
                Q_ARG("QVariant", actionId),
                Q_ARG("QVariant", props),
            )

    def removeAction(self, actionId: str):
        """按 ID 删除单个菜单项 Remove a single action by ID"""
        self._actions = [
            action for action in self._actions if action.get("actionId") != actionId
        ]
        self._callbacks.pop(actionId, None)
        if self._qml_menu:
            QMetaObject.invokeMethod(
                self._qml_menu, "removeAction", Q_ARG("QVariant", actionId)
            )

    def setActionChecked(self, actionId: str, checked: bool):
        """设置菜单项的勾选状态 Set menu item checked state"""
        self.updateAction(actionId, checked=checked)

    def setActionEnabled(self, actionId: str, enabled: bool):
        """设置菜单项的启用状态 Set menu item enabled state"""
        self.updateAction(actionId, enabled=enabled)

    def setActionText(self, actionId: str, text: str):
        """设置菜单项的文本 Set menu item text"""
        self.updateAction(actionId, text=text)

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
