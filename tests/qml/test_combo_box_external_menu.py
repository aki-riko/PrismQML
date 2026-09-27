# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ComboBox 挂载外部 MenuCore 的真实交互合同。

ComboBox 与 Button 使用同一份外部菜单契约(isOpen / openAtControl / close), 因此挂上
MenuCore 后级联能力完全由菜单栈提供: 逐层嵌套、悬停展开、锚定定位与收起; 控件只负责把
选中的叶子回填到自己的字段。
用法: python scripts/test_process.py --qt-platform offscreen --timeout 180 -- python -m pytest tests/qml/test_combo_box_external_menu.py
"""
from pathlib import Path

import pytest

from combo_box_core_conventions_shared import (
    _pump,
    _wait_for,
)
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtWidgets import QApplication

REPO_ROOT = Path(__file__).resolve().parents[2]

SCENE_SOURCE = b"""
import PrismQML
import PrismQML.controls.menus
import QtQuick
import QtQuick.Window

Window {
    width: 520
    height: 320
    visible: true

    // The attached menu owns the cascade; the combo box only reports the leaf it gets.
    MenuCore {
        id: cascadeMenu
        objectName: "comboBoxExternalMenu"
        useInWindowPopup: true
        Component.onCompleted: addNodes([
            { text: "File", children: [
                { text: "New" },
                { text: "Open" } ] },
            { text: "Tools", children: [
                { text: "Developer", children: [
                    { text: "Inspect" },
                    { text: "Console" } ] },
                { text: "Options" } ] },
            { text: "Help" }
        ], [])
    }

    ComboBox {
        id: combo
        objectName: "externalMenuCombo"
        x: 30
        y: 30
        width: 220
        model: ["fallback-item"]
        placeholderText: "Select"
        menu: cascadeMenu
    }

    QtObject { id: invalidMenu; objectName: "invalidComboMenu" }

    ComboBox {
        id: invalidCombo
        objectName: "invalidMenuCombo"
        x: 30
        y: 100
        width: 220
        model: ["Alpha", "Beta"]
        menu: invalidMenu
    }

    // Report the cascade shape as plain data, so a test never reaches into internals and
    // no QObject crosses the language boundary.
    readonly property var cascadeShape: {
        var topRows = cascadeMenu._menuItems()
        var top = []
        for (var i = 0; i < topRows.length; i++) {
            var row = topRows[i]
            var entry = { "text": row.text, "hasSubmenu": row.hasSubmenu, "children": [] }
            if (row._level) {
                var midRows = row._level._menuItems()
                for (var j = 0; j < midRows.length; j++) {
                    var mid = midRows[j]
                    var midEntry = {
                        "text": mid.text,
                        "hasSubmenu": mid.hasSubmenu,
                        "actionId": mid.actionId,
                        "children": []
                    }
                    if (mid._level) {
                        var lowRows = mid._level._menuItems()
                        for (var k = 0; k < lowRows.length; k++) {
                            midEntry.children.push({
                                "text": lowRows[k].text,
                                "actionId": lowRows[k].actionId
                            })
                        }
                    }
                    entry.children.push(midEntry)
                }
            }
            top.push(entry)
        }
        return top
    }
}
"""


@pytest.fixture(scope="module")
def scene():
    app = QApplication.instance() or QApplication([])
    engine = None
    window = None
    try:
        import prismqml
        from prismqml import register_types

        prismqml.configure_qml_environment()
        engine = QQmlApplicationEngine()
        engine.addImportPath(str(REPO_ROOT / "prismqml"))
        register_types(engine)
        component = QQmlComponent(engine)
        component.setData(
            SCENE_SOURCE,
            QUrl.fromLocalFile(str(REPO_ROOT / "tests" / "qml" / "combo-external-menu.qml")),
        )
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        window = component.create()
        assert isinstance(window, QQuickWindow), [
            error.toString() for error in component.errors()
        ]
        window.requestActivate()
        assert _wait_for(window.isActive)
        _pump(120)
        yield window
    finally:
        if window is not None:
            window.close()
            window.deleteLater()
        del engine, app


def _read(item: QQuickItem, name: str):
    """读取 QML 属性为原生 Python 值（数组/对象经 QJSValue 返回）。"""
    value = item.property(name)
    return value.toVariant() if hasattr(value, "toVariant") else value


def _shape(scene: QQuickWindow) -> list:
    """场景以纯数据上报的级联形态。"""
    return _read(scene, "cascadeShape") or []


def _control(container: QQuickItem) -> QQuickItem:
    """入口容器里的实际控件: ComboBox 只做转发, 状态与弹层都在被加载的控件上。"""
    if container.metaObject().indexOfProperty("_popup") >= 0:
        return container
    for child in container.children():
        if child.metaObject().className().startswith("QQuickLoader"):
            loaded = child.property("item")
            if isinstance(loaded, QQuickItem):
                return loaded
    raise AssertionError("未找到入口容器的内部控件")


def _menu(root: QQuickWindow) -> QQuickItem:
    menu = root.findChild(QQuickItem, "comboBoxExternalMenu")
    assert menu is not None, "外部菜单未注册"
    return menu


def _open(container: QQuickItem, menu: QQuickItem) -> QQuickItem:
    combo = _control(container)
    combo.openPopup()
    assert _wait_for(lambda: _read(menu, "isOpen") is True), "外部菜单未打开"
    return combo


def _close(combo: QQuickItem, menu: QQuickItem) -> None:
    combo.closePopup()
    _wait_for(lambda: _read(menu, "isOpen") is False)
    _pump(120)


def test_attached_menu_owns_the_dropdown(scene):
    """挂上 MenuCore 后, 展开的是菜单本身, 且级联层由它持有。"""
    menu = _menu(scene)
    combo = _open(scene.findChild(QQuickItem, "externalMenuCombo"), menu)
    try:
        assert _read(combo, "isOpen") is True, "控件未记录展开状态"
        shape = _shape(scene)
        assert [entry["text"] for entry in shape] == ["File", "Tools", "Help"]
        states = {entry["text"]: bool(entry["hasSubmenu"]) for entry in shape}
        assert states == {"File": True, "Tools": True, "Help": False}
    finally:
        _close(combo, menu)


def test_child_level_is_reachable_and_leaf_fills_field(scene):
    """父行持有自己的层级; 深层叶子以完整路径寻址并回填字段。"""
    menu = _menu(scene)
    combo = _open(scene.findChild(QQuickItem, "externalMenuCombo"), menu)
    try:
        shape = _read(scene, "cascadeShape")
        tools = next(entry for entry in shape if entry["text"] == "Tools")
        assert [child["text"] for child in tools["children"]] == [
            "Developer", "Options"
        ], f"第二层不符: {tools['children']}"
        developer = next(
            child for child in tools["children"] if child["text"] == "Developer"
        )
        assert developer["hasSubmenu"] is True
        assert [child["text"] for child in developer["children"]] == [
            "Inspect", "Console"
        ], f"第三层不符: {developer['children']}"

        # 叶子 id 携带自根起的路径, 控件据此还原用户走过的路径。
        console = next(
            child for child in developer["children"] if child["text"] == "Console"
        )
        action_id = console["actionId"]
        assert action_id.startswith("leaf:"), f"叶子未按路径寻址: {action_id!r}"
        assert action_id[5:].split("\u0001") == ["Tools", "Developer", "Console"], (
            f"叶子路径不符: {action_id!r}"
        )

        # 菜单提交叶子时经 actionTriggered 上报, 控件据此回填并收起。
        menu.actionTriggered.emit(action_id)
        assert _wait_for(lambda: _read(combo, "currentText") == "Console"), (
            f"字段未回填: {_read(combo, 'currentText')!r}"
        )
        assert _wait_for(lambda: _read(menu, "isOpen") is False), "菜单未收起"
    finally:
        _close(combo, menu)


def test_invalid_menu_degrades_to_builtin_list(scene):
    """误传非菜单对象时退化为内置候选列表, 而不是让下拉失效。"""
    container = scene.findChild(QQuickItem, "invalidMenuCombo")
    combo = _control(container)
    combo.openPopup()
    try:
        assert _wait_for(lambda: _read(combo, "isOpen") is True), "内置候选未展开"
        assert combo.metaObject().indexOfProperty("_popup") >= 0, "内置弹层入口缺失"
    finally:
        combo.closePopup()
        _wait_for(lambda: _read(combo, "isOpen") is False)
