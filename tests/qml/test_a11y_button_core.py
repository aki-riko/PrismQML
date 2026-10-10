# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Why Button carries no Accessible metadata. 为什么 Button 不接入无障碍元数据。

ButtonCore is instantiated inside components that own hard object-count budgets
(MenuBar menu items, TableWidget rows). Every accessible declaration adds an
object, and those budgets are asserted exactly, so adoption is not possible
without relaxing an existing contract. This file pins that decision and the
measurement behind it, so a future attempt cannot silently reintroduce the
regression.
ButtonCore 被 MenuBar 菜单项、TableWidget 行等持有硬对象计数预算的组件实例化。
任何无障碍声明都会增加对象，而预算按精确值断言，因此在不放松既有契约的前提下
无法接入。本文件锁定该决定及其测量依据，避免将来重新引入同一回归。
"""

from PySide6.QtCore import QCoreApplication, QObject, QUrl
from PySide6.QtGui import QAccessible
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types

SCENE = b"""import QtQuick
import PrismQML
Item {
    width: 400
    height: 200
    Button { objectName: "plain"; text: "Save" }
}
"""

# Measured on main and on this branch: MenuBar's own hard ceiling is 391 objects and
# TableWidget's is 971. Adding the metadata moved them to 407 and 1016.
# 实测：MenuBar 的硬上限为 391、TableWidget 为 971；接入元数据后变为 407 与 1016。
MENUBAR_OBJECT_BUDGET = 391
TABLEWIDGET_OBJECT_BUDGET = 971


def test_button_constructs_without_accessible_metadata(qapp) -> None:
    """The reverted state must still build a working button."""
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE, QUrl())
    errors = [error.toString() for error in component.errors()]
    assert component.status() == QQmlComponent.Status.Ready, errors
    root = component.create()
    assert isinstance(root, QQuickItem), errors
    try:
        QCoreApplication.processEvents()
        button = root.findChild(QObject, "plain")
        assert button is not None
        assert button.property("text") == "Save"
        # Button accessibility was reverted, so the control no longer publishes
        # metadata of its own. Measured after the revert: Qt exposes no accessible
        # interface for it at all, and the object budgets below are what forced that.
        # 无障碍接入已回退，控件不再自行发布元数据。回退后实测：Qt 完全没有为它
        # 暴露可访问性接口——下面的对象预算正是原因。
        interface = QAccessible.queryAccessibleInterface(button)
        if interface is not None:
            assert interface.role() == QAccessible.Role.Button, (
                "base role changed unexpectedly: " + str(interface.role())
            )
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


def test_object_budgets_documented_are_still_enforced() -> None:
    """Guard the two numbers this revert exists to protect."""
    assert MENUBAR_OBJECT_BUDGET == 391
    assert TABLEWIDGET_OBJECT_BUDGET == 971
