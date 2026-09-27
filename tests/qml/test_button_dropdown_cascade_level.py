# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Dropdown Button 内联菜单级联子菜单真实交互合同。

验证真实行为：带 children 的菜单项显示子菜单箭头、打开更深层级、叶子提交被记录并
关闭整条级联、关闭菜单时子层被拆除。层级是独立原生弹层表面，offscreen 平台不显示
第二个原生表面，因此按各层真实行内容判定层级是否打开。
用法: python scripts/test_process.py --qt-platform offscreen --timeout 180 -- python -m pytest tests/qml/test_button_dropdown_cascade_menu.py
"""
from pathlib import Path

import pytest

from _button_dropdown_prewarm_support import (
    _button,
    _button_dropdown,
    _create_scene,
    _pump,
    _visual_descendants,
    _wait_for,
)
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

REPO_ROOT = Path(__file__).resolve().parents[2]

CASCADE_ITEMS = [
    {
        "text": "File",
        "children": [{"text": "New"}, {"text": "Open"}],
    },
    {
        "text": "Tools",
        "children": [
            {"text": "Developer"},
            {"text": "Options"},
        ],
    },
    {"text": "Help"},
]

ROOT_TEXTS = ["File", "Tools", "Help"]
CHILD_TEXTS = ["Developer", "Options"]


@pytest.fixture
def cascade_scene(qapp):
    engine, component, root, warnings = _create_scene()
    window = QQuickWindow()
    window.setWidth(420)
    window.setHeight(300)
    root.setParentItem(window.contentItem())
    window.show()
    window.requestActivate()
    _pump(30)
    try:
        yield root, window, warnings
    finally:
        window.close()
        window.deleteLater()
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


def _read(item: QQuickItem, name: str):
    """读取 QML 属性为原生 Python 值（PySide6 对部分属性返回包装对象）。"""
    value = item.property(name)
    return value.toVariant() if hasattr(value, "toVariant") else value


def _descendants(item):
    result = []
    pending = list(item.children())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.children())
    return result


def _cascade_rows(window: QQuickWindow) -> list[QQuickItem]:
    """窗口内的级联行（按屏幕纵向排序）。

    根层行是 MenuDelegate, 更深层级是 CascadeItemDelegate; 两者都带
    text / hasSubmenu, 以这组属性识别, 不绑定具体类型。
    """
    rows = [
        item
        for item in _visual_descendants(window.contentItem())
        if item.metaObject().indexOfProperty("hasSubmenu") >= 0
        and item.metaObject().indexOfProperty("text") >= 0
    ]
    return sorted(
        rows,
        key=lambda item: item.mapToItem(window.contentItem(), 0, 0).y(),
    )


def _row_texts(window: QQuickWindow) -> list[str]:
    return [str(_read(row, "text")) for row in _cascade_rows(window)]


def _row_centre(window: QQuickWindow, row: QQuickItem) -> QPoint:
    point = row.mapToItem(
        window.contentItem(), QPointF(row.width() / 2, row.height() / 2)
    )
    return QPoint(round(point.x()), round(point.y()))


def _all_level_rows() -> list[list[str]]:
    dump: list[list[str]] = []
    for window in QGuiApplication.allWindows():
        if not isinstance(window, QQuickWindow):
            continue
        try:
            texts = _row_texts(window)
        except RuntimeError:
            continue
        if texts:
            dump.append(texts)
    return dump


def _wait_for_rows(expected: list[str], timeout_ms: int = 3000) -> QQuickWindow:
    holder: list[QQuickWindow] = []

    def ready() -> bool:
        for window in QGuiApplication.allWindows():
            if not isinstance(window, QQuickWindow):
                continue
            try:
                if _row_texts(window) == expected:
                    holder.append(window)
                    return True
            except RuntimeError:
                continue
        return False

    assert _wait_for(ready, timeout_ms), (
        f"未找到列出 {expected} 的层级; 现有层级={_all_level_rows()}"
    )
    return holder[-1]


def _menu_popup(dropdown: QQuickItem) -> QQuickItem:
    matches = [
        child
        for child in _descendants(dropdown)
        if child.metaObject().indexOfProperty("_itemsHeight") >= 0
        and child.metaObject().indexOfProperty("_prewarmed") >= 0
    ]
    assert len(matches) == 1, [c.metaObject().className() for c in matches]
    return matches[0]


def _setup_cascade(button: QQuickItem, dropdown: QQuickItem) -> None:
    button.setProperty("menuItems", CASCADE_ITEMS)
    # 内联菜单内容按需创建, 先请求一次使委托生成。
    dropdown.prewarmMenu()
    _pump(120)


def _open_menu(dropdown: QQuickItem) -> None:
    """展开按钮内联菜单并确认根层已渲染出行。

    按钮菜单渲染在 Qt 管理的弹层窗口里(Popup.Window), 不是 PopupWindowCore 自建的
    原生表面, 因此经窗口内容定位其层级。
    """
    dropdown.openMenu()
    popup = _menu_popup(dropdown)
    assert _wait_for(lambda: _read(popup, "isOpen") is True), "菜单未打开"
    _wait_for_rows(ROOT_TEXTS)
    _pump(120)


def _close_menu(dropdown: QQuickItem) -> None:
    """经组件自身的关闭入口收起菜单。

    直接操作弹层不会经过宿主的拆除路径, 而这里要固定的正是宿主在关闭时做了什么。
    """
    popup = _menu_popup(dropdown)
    if _read(popup, "isOpen") is True:
        # 与菜单自身关闭同一条路径: 宿主先拆除自己的级联层级, 再收起菜单。
        dropdown._closeInternalMenu()
    _wait_for(lambda: _read(popup, "isOpen") is False)
    _pump(240)


def _open_child_level(dropdown: QQuickItem) -> tuple[QQuickWindow, QQuickWindow]:
    """请求展开 "Tools" 的子层, 返回 (根层窗口, 子层窗口)。

    层级由悬停打开; offscreen 平台对第二个原生表面的悬停投递不稳定, 因此这里按下父行,
    走的是同一条打开路径（父行的按下也是对展开的显式请求）。
    """
    menu_window = _wait_for_rows(ROOT_TEXTS)
    owner = next(
        row for row in _cascade_rows(menu_window) if _read(row, "text") == "Tools"
    )
    QTest.mouseClick(
        menu_window, Qt.MouseButton.LeftButton, pos=_row_centre(menu_window, owner)
    )
    child_window = _wait_for_rows(CHILD_TEXTS)
    # 子层与根层是不同的原生表面。
    assert child_window is not menu_window
    return menu_window, child_window


def test_items_with_children_show_submenu_arrow(cascade_scene):
    root, _window, _warnings = cascade_scene
    button = _button(root, "dropdownButton")
    dropdown = _button_dropdown(button)
    _setup_cascade(button, dropdown)
    _open_menu(dropdown)
    try:
        menu_window = _wait_for_rows(ROOT_TEXTS)
        states = {
            str(_read(row, "text")): bool(_read(row, "hasSubmenu"))
            for row in _cascade_rows(menu_window)
        }
        # 带 children 的项显示子菜单箭头, 纯标签项不显示。
        assert states == {"File": True, "Tools": True, "Help": False}
    finally:
        _close_menu(dropdown)


def test_opening_child_level_records_leaf_commit(cascade_scene):
    """打开子层并提交叶子项: 记录所属根项下标与叶子文本, 并关闭整条级联。

    子层的打开走真实交互; 叶子的提交由行委托自身的点击契约驱动——offscreen 平台对
    第二个原生表面的鼠标投递不可靠, 而这里要固定的是"叶子提交后系统做了什么"。
    """
    root, _window, _warnings = cascade_scene
    button = _button(root, "dropdownButton")
    dropdown = _button_dropdown(button)
    _setup_cascade(button, dropdown)

    _open_menu(dropdown)
    try:
        _menu_window, child_window = _open_child_level(dropdown)
        leaf = next(
            row for row in _cascade_rows(child_window)
            if _read(row, "text") == "Options"
        )
        leaf.clicked.emit()
        assert _wait_for(
            lambda: _read(dropdown, "_lastSubmenuCommit") is not None, 1500
        ), "级联提交未被记录"
        commit = _read(dropdown, "_lastSubmenuCommit")
        assert commit == {"parentIndex": 1, "text": "Options"}, f"提交记录不符: {commit}"
        popup = _menu_popup(dropdown)
        assert _wait_for(lambda: _read(popup, "isOpen") is False), "菜单未关闭"
    finally:
        _close_menu(dropdown)


def test_closing_menu_tears_down_cascade(cascade_scene):
    root, _window, _warnings = cascade_scene
    button = _button(root, "dropdownButton")
    dropdown = _button_dropdown(button)
    _setup_cascade(button, dropdown)
    _open_menu(dropdown)
    try:
        _open_child_level(dropdown)
        # 宿主收起菜单时同步拆除自己的级联层级。
        dropdown._closeInternalMenu()
        assert _wait_for(
            lambda: dropdown.property("_submenuPanel") is None, 2000
        ), "关闭菜单后子层未被拆除"
    finally:
        _close_menu(dropdown)
