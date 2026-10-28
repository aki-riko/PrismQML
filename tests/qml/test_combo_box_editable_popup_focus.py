# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""可编辑下拉的候选弹层与输入焦点过滤器。

`input_focus_filter` 在鼠标按下位置**不属于当前焦点输入框**时清掉该输入框焦点。
可编辑下拉的候选层是**独立原生窗口**：点它天然落在输入框矩形之外，于是过滤器会把
焦点清掉，`ComboBoxCore` 的失焦守卫随即收起刚被点击的弹层 —— 用户看到的症状就是
「点分类行展开，候选层直接消失」。

因此过滤器的清除范围必须限制在**输入框所属窗口**内：本应用其它窗口（弹层/菜单）
的按下事件属于该输入控件自己的交互，不得清它的焦点。同一窗口内的外部点击仍要清，
否则「点页面空白处收起候选」会坏掉 —— 两个方向都要有回归。
"""

from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPoint,
    QPointF,
    QTimer,
    Qt,
    QUrl,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types
from prismqml.python.core.input_focus_filter import install_input_focus_filter


ROOT = Path(__file__).resolve().parents[2]

SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: scene

    width: 520
    height: 360
    visible: true
    color: "#ffffff"

    ComboBoxTree {
        id: combo
        objectName: "editableCombo"
        x: 40
        y: 40
        width: 240
        editable: true
        searchEnabled: true
        searchPlaceholder: "search account"
        model: [
            {
                "text": "Category A",
                "children": [{"text": "Account A1"}, {"text": "Account A2"}]
            },
            {
                "text": "Category B",
                "children": [{"text": "Account B1"}]
            }
        ]
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1600) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return bool(predicate())


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _rows(combo: QQuickItem) -> list:
    return list(_variant(combo.property("_flatModel")) or [])


def _expanded(combo: QQuickItem):
    return dict(_variant(combo.property("_expandedNodes")) or {})


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, QUrl("combo-box-editable-popup-focus.qml"))
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isActive)
    _pump(120)
    combo = window.findChild(QQuickItem, "editableCombo")
    assert combo is not None
    return engine, component, window, combo, warnings


def _dispose_scene(engine, component, window, combo) -> None:
    if combo is not None and combo.property("isOpen"):
        combo.closePopup()
        _wait_for(lambda: not combo.property("isOpen"))
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(60)


def _new_visible_windows(windows_before):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
    ]


def _point_in(window: QQuickWindow, item: QQuickItem, x: float, y: float) -> QPoint:
    point = item.mapToItem(window.contentItem(), QPointF(x, y))
    return QPoint(round(point.x()), round(point.y()))


def _open_popup(window, combo: QQuickItem, windows_before):
    """点下拉箭头展开候选（editable 模式只有右端箭头区响应点击）。"""
    arrow_point = _point_in(
        window, combo, combo.width() - 10, combo.height() / 2
    )
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, arrow_point
    )
    assert _wait_for(lambda: combo.property("isOpen")), "候选层没有打开"
    _pump(120)
    popup_windows = [
        candidate
        for candidate in _new_visible_windows(windows_before)
        if candidate.transientParent() is window
    ]
    assert len(popup_windows) == 1, [w.title() for w in popup_windows]
    return popup_windows[0]


def _parent_row(popup_window: QQuickWindow):
    """弹层里第一个「有子节点」的可见行（级联菜单的分类行）。"""
    stack = [popup_window.contentItem()]
    candidates = []
    while stack:
        item = stack.pop()
        meta = item.metaObject()
        if (
            meta.indexOfProperty("hasChildren") >= 0
            and meta.indexOfProperty("expanded") >= 0
            and meta.indexOfProperty("depth") >= 0
        ):
            if item.property("hasChildren") and item.isVisible() and item.height() > 0:
                candidates.append(item)
        stack.extend(item.childItems())
    assert candidates, "弹层里没有分类行"
    candidates.sort(key=lambda item: item.mapToScene(QPointF(0, 0)).y())
    return candidates[0]


def test_clicking_parent_row_keeps_editable_popup_open(qapp):
    """点分类行只展开，不收起候选层（输入框焦点必须留在原位）。"""
    install_input_focus_filter(qapp)
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, combo, warnings = _create_scene()
    try:
        # `ComboBoxTree` 初始化时默认全展开，这里折叠成「分类行」形态。
        combo.setProperty("_expandedNodes", {})
        assert _wait_for(lambda: len(_rows(combo)) == 2)

        popup_window = _open_popup(window, combo, windows_before)
        assert combo.property("focused") is True, "候选展开后输入框应持有焦点"

        row = _parent_row(popup_window)
        before_expanded = _expanded(combo)
        QTest.mouseClick(
            popup_window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            _point_in(popup_window, row, 18, row.height() / 2),
        )
        _pump(150)

        assert _expanded(combo) != before_expanded, "点击没有落在分类行上"
        assert combo.property("isOpen") is True, (
            "点分类行后候选层不应收起（输入焦点过滤器不得清掉可编辑下拉的焦点）"
        )
        assert combo.property("focused") is True
        assert len(_rows(combo)) == 4
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window, combo)


def test_clicking_same_window_blank_area_still_dismisses_popup(qapp):
    """同一窗口内的外部点击仍要清焦点并收起候选。"""
    install_input_focus_filter(qapp)
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, combo, warnings = _create_scene()
    try:
        combo.setProperty("_expandedNodes", {})
        assert _wait_for(lambda: len(_rows(combo)) == 2)
        # 🔴 弹层窗口的 Python wrapper 必须一直持有: PySide 对
        # `topLevelWindows()` 拿到的包装一旦被回收, 会把那个原生窗口一并销毁,
        # 连带本场景的 wrapper 全部失效(2026-10-28 实测)。
        popup_window = _open_popup(window, combo, windows_before)
        assert popup_window.isVisible()

        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(window.width() - 20, window.height() - 20),
        )
        assert _wait_for(lambda: not combo.property("isOpen")), (
            "点页面空白处必须收起候选层"
        )
        assert combo.property("focused") is False
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window, combo)

