# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""TreeView/TreeWidget pointer gesture regressions. 树形视图指针手势回归。"""

from PySide6.QtCore import QEventLoop, QObject, QPointF, Qt, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from prismqml import register_types


SCENE_URL = QUrl("inline:tree-pointer-gestures.qml")
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Window {
    id: window
    width: 640
    height: 420
    visible: true
    color: "white"

    property int widgetDoubleClicks: 0

    TreeView {
        id: treeView
        objectName: "treeView"
        x: 10
        y: 10
        width: 280
        height: 360
        model: [
            {
                text: "Root", expanded: false, children: [
                    { text: "Alpha" },
                    { text: "Beta" }
                ]
            },
            { text: "Second" },
            { text: "Third" }
        ]
    }

    TreeWidget {
        id: treeWidget
        objectName: "treeWidget"
        x: 320
        y: 10
        width: 280
        height: 360
        model: [
            {
                text: "Root", expanded: false, children: [
                    { text: "Alpha" },
                    { text: "Beta" }
                ]
            },
            { text: "Second" },
            { text: "Third" }
        ]
        onItemDoubleClicked: window.widgetDoubleClicks += 1
    }
}
"""


def _pump(milliseconds: int = 40) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def _rows(list_model) -> list[dict]:
    roles = {
        int(role_id): bytes(name).decode("utf-8")
        for role_id, name in list_model.roleNames().items()
    }
    result = []
    for index in range(list_model.rowCount()):
        model_index = list_model.index(index, 0)
        result.append(
            {
                name: _variant(list_model.data(model_index, role_id))
                for role_id, name in roles.items()
            }
        )
    return result


def _shape(rows: list[dict]) -> list[tuple]:
    return [
        (row.get("text"), int(row.get("depth") or 0), bool(row.get("expanded")))
        for row in rows
    ]


def _delegate(root: QQuickItem, text: str) -> QQuickItem:
    for item in _descendants(root):
        if item.metaObject().indexOfProperty("itemText") < 0:
            continue
        if item.property("itemText") == text:
            return item
    raise AssertionError(f"delegate not found: {text}")


def _mouse_area(delegate: QQuickItem) -> QQuickItem:
    for item in _descendants(delegate):
        meta = item.metaObject()
        if (
            meta.indexOfProperty("expandEnd") >= 0
            or meta.indexOfProperty("expandBtnStart") >= 0
        ):
            return item
    raise AssertionError("expand mouse area not found")


def _zone_x(mouse_area: QQuickItem) -> float:
    if mouse_area.metaObject().indexOfProperty("expandEnd") >= 0:
        return float(mouse_area.property("expandEnd")) - 2.0
    start = float(mouse_area.property("expandBtnStart"))
    end = float(mouse_area.property("expandBtnEnd"))
    return (start + end) / 2.0


def _point(root: QQuickItem, text: str, zone: bool) -> QPointF:
    delegate = _delegate(root, text)
    mouse_area = _mouse_area(delegate)
    local_x = _zone_x(mouse_area) if zone else delegate.width() - 20.0
    return delegate.mapToScene(QPointF(local_x, delegate.height() / 2.0))


def _settle_pointer(window) -> None:
    # Move away and outlast the double-click interval so clicks stay independent.
    # 移开指针并超过双击间隔，保证每次点击都被识别为独立单击。
    QTest.mouseMove(window, QPointF(4, 4).toPoint())
    _pump(600)


def _click(window, root: QQuickItem, text: str, zone: bool) -> None:
    _settle_pointer(window)
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _point(root, text, zone).toPoint(),
    )
    _pump(200)


def _double_click(window, root: QQuickItem, text: str, zone: bool) -> None:
    _settle_pointer(window)
    QTest.mouseDClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _point(root, text, zone).toPoint(),
    )
    _pump(200)


def _create_scene(engine, qapp):
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    for _ in range(200):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert window is not None, [error.toString() for error in component.errors()]
    for _ in range(50):
        if window.isVisible():
            break
        _pump()
    _pump(200)
    tree_view = window.findChild(QObject, "treeView")
    tree_widget = window.findChild(QObject, "treeWidget")
    assert tree_view is not None and tree_widget is not None
    for _ in range(100):
        if _rows(tree_view.property("listModel")):
            break
        _pump()
    return component, window, tree_view, tree_widget


def test_tree_widget_expand_zone_double_click_toggles_once(qapp):
    """Double click must toggle once, not twice. 双击须只切换一次而非两次。"""
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, window, _tree_view, tree_widget = _create_scene(engine, qapp)
    try:
        assert _shape(
            [
                _variant(tree_widget._getItemObject(index))
                for index in range(tree_widget.count())
            ]
        ) == [
            ("Root", 0, False),
            ("Second", 0, False),
            ("Third", 0, False),
        ]

        _double_click(window, tree_widget, "Root", zone=True)
        assert tree_widget.count() == 5
        assert window.property("widgetDoubleClicks") == 1

        _double_click(window, tree_widget, "Root", zone=True)
        assert tree_widget.count() == 3
        assert window.property("widgetDoubleClicks") == 2

        # Double click on the label keeps the historical toggle behaviour.
        # 文本区双击保持既有切换行为。
        _double_click(window, tree_widget, "Root", zone=False)
        assert tree_widget.count() == 5
        assert window.property("widgetDoubleClicks") == 3

        # A single click on the label still only selects. 文本区单击仍只选中。
        _click(window, tree_widget, "Root", zone=False)
        assert tree_widget.count() == 5

        # A single click on the expand zone still toggles. 按钮区单击仍切换。
        _click(window, tree_widget, "Root", zone=True)
        assert tree_widget.count() == 3
        assert window.property("widgetDoubleClicks") == 3
    finally:
        window.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump(1)


def test_tree_view_expand_zone_double_click_toggles_once(qapp):
    """TreeView default delegate must match the TreeWidget gesture contract.

    TreeView 默认委托须与 TreeWidget 手势契约一致。
    """
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, window, tree_view, _tree_widget = _create_scene(engine, qapp)
    try:
        list_model = tree_view.property("listModel")
        assert _shape(_rows(list_model)) == [
            ("Root", 0, False),
            ("Second", 0, False),
            ("Third", 0, False),
        ]

        _double_click(window, tree_view, "Root", zone=True)
        assert _shape(_rows(list_model)) == [
            ("Root", 0, True),
            ("Alpha", 1, False),
            ("Beta", 1, False),
            ("Second", 0, False),
            ("Third", 0, False),
        ]

        _double_click(window, tree_view, "Root", zone=True)
        assert _shape(_rows(list_model)) == [
            ("Root", 0, False),
            ("Second", 0, False),
            ("Third", 0, False),
        ]

        _double_click(window, tree_view, "Root", zone=False)
        assert tree_view.count() == 5

        _click(window, tree_view, "Root", zone=False)
        assert tree_view.count() == 5

        _click(window, tree_view, "Root", zone=True)
        assert tree_view.count() == 3
    finally:
        window.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump(1)
