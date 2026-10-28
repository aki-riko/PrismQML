# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""树形下拉的两件事：可编辑输入框即搜索、展开/收起有行级动画。

背景（2026-10-28，幻灵匣「百战助手」账号框实测）：
1. 可编辑模式下候选展开期间焦点留在宿主输入框（弹层不抢焦点），而过滤只由弹层里的
   `PopupSearchBox` 驱动 → 在字段里打字根本不收窄树，「搜索账号」框等于摆设。
2. 展开/折叠只改 `_flatModel`（整表替换），ListView 直接重建委托，既没有增删过渡也
   没有让位动画；弹层高度一旦顶到 `treePopupHeight`（滚动条接管），高度动画也无从发生，
   用户看到的就是「一下子全出来」。
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
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "ComboBox"
    / "ComboBoxTree.qml"
)

SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: scene

    readonly property int expectedRowHeight: Enums.comboBoxMetrics.itemHeight

    width: 560
    height: 460
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
        model: [
            {"text": "666", "children": [{"text": "acc-a"}, {"text": "acc-b"}]},
            {"text": "888", "children": [{"text": "acc-c"}, {"text": "acc-d"}]},
            {"text": "work", "children": [{"text": "acc-e"}]}
        ]
    }
}
"""


def _pump(milliseconds: int = 16) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1600) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 16
    return bool(predicate())


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _rows(combo: QQuickItem) -> list:
    return list(_variant(combo.property("_flatModel")) or [])


def _texts(combo: QQuickItem) -> list:
    return [row["text"] for row in _rows(combo)]


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, QUrl("combo-box-tree-rows.qml"))
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
    combo.setProperty("_expandedNodes", {})
    assert _wait_for(lambda: len(_rows(combo)) == 3)
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


def _point_in(window: QQuickWindow, item: QQuickItem, x: float, y: float) -> QPoint:
    point = item.mapToItem(window.contentItem(), QPointF(x, y))
    return QPoint(round(point.x()), round(point.y()))


def _open_popup(window, combo: QQuickItem, windows_before):
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _point_in(window, combo, combo.width() - 10, combo.height() / 2),
    )
    assert _wait_for(lambda: combo.property("isOpen")), "候选层没有打开"
    _pump(140)
    popup_windows = [
        candidate
        for candidate in QGuiApplication.topLevelWindows()
        if candidate.isVisible()
        and not any(candidate is existing for existing in windows_before)
        and candidate.transientParent() is window
    ]
    assert len(popup_windows) == 1, [w.title() for w in popup_windows]
    return popup_windows[0]


def _row_items(popup_window: QQuickWindow) -> list:
    found = []
    stack = [popup_window.contentItem()]
    while stack:
        item = stack.pop()
        meta = item.metaObject()
        if meta.indexOfProperty("hasChildren") >= 0 and meta.indexOfProperty("depth") >= 0:
            if item.isVisible():
                found.append(item)
        stack.extend(item.childItems())
    found.sort(key=lambda item: item.mapToScene(QPointF(0, 0)).y())
    return found


def _row_by_text(popup_window: QQuickWindow, text: str):
    for item in _row_items(popup_window):
        if item.property("text") == text:
            return item
    return None


def test_typing_in_editable_field_filters_the_tree(qapp):
    """在可编辑输入框里打字就收窄树；关掉再开不带着过期查询。"""
    install_input_focus_filter(qapp)
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, combo, warnings = _create_scene()
    try:
        popup_window = _open_popup(window, combo, windows_before)
        assert _texts(combo) == ["666", "888", "work"]

        QTest.keyClick(window, Qt.Key.Key_8)
        QTest.keyClick(window, Qt.Key.Key_8)
        assert _wait_for(lambda: _texts(combo) == ["888"]), _texts(combo)
        assert combo.property("_searchText") == "88"
        assert combo.property("isOpen") is True
        assert _wait_for(lambda: _row_by_text(popup_window, "666") is None), (
            "收窄后旧的分类行必须从弹层里消失"
        )

        # 收起候选后查询必须丢弃：下一次展开是全量候选。
        # 查询要活过收起动画（否则收起中的列表会跳回全量），所以等 popupVisible 归零。
        combo.closePopup()
        assert _wait_for(lambda: not combo.property("popupVisible"))
        assert combo.property("_searchText") == ""
        popup_window = _open_popup(window, combo, windows_before)
        assert _texts(combo) == ["666", "888", "work"]
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window, combo)


def test_expanding_parent_animates_rows_instead_of_jumping(qapp):
    """展开分类：下面的行先平滑让位，新行再淡入（不是一秒全出来）。"""
    install_input_focus_filter(qapp)
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, combo, warnings = _create_scene()
    try:
        popup_window = _open_popup(window, combo, windows_before)
        row_height = window.property("expectedRowHeight")
        assert row_height > 0

        tail_before = _row_by_text(popup_window, "888")
        assert tail_before is not None
        before_y = tail_before.mapToScene(QPointF(0, 0)).y()

        combo._toggleExpand("root_0")

        # 逐帧采样：新行必须从「透明」淡入（否则它会立刻压在正在让位的旧行身上，
        # 出现文字重影）；被展开行下方的行必须经过中间位置（让位动画，而不是瞬移）。
        min_new_opacity = 1.0
        max_new_opacity = 0.0
        moved_y = []
        for _ in range(14):
            _pump(16)
            new_row = _row_by_text(popup_window, "acc-a")
            if new_row is not None:
                min_new_opacity = min(min_new_opacity, new_row.opacity())
                max_new_opacity = max(max_new_opacity, new_row.opacity())
            tail = _row_by_text(popup_window, "888")
            if tail is not None:
                moved_y.append(tail.mapToScene(QPointF(0, 0)).y())

        final_y = before_y + 2 * row_height
        assert min_new_opacity <= 0.05, (
            f"新行的第一帧必须是透明的，实测最小 opacity={min_new_opacity}"
        )
        assert max_new_opacity >= 0.99, (
            f"新行没有淡入完成，实测最大 opacity={max_new_opacity}"
        )
        assert moved_y, "下方的行在动画期间不可见，弹层状态异常"
        assert any(before_y + 0.5 < y < final_y - 0.5 for y in moved_y), (
            f"让位动画没有经过中间位置：起点 {before_y}、终点 {final_y}、采样 {moved_y}"
        )
        assert abs(moved_y[-1] - final_y) < 0.5, (
            f"稳定位置不对：期望 {final_y}，实际 {moved_y[-1]}"
        )
        assert len(_texts(combo)) == 5
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window, combo)


def test_tree_rows_use_incremental_model_and_transitions():
    """源码契约：行视图模型增量同步 + 过渡顺序（先让位、再淡入）。"""
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert "ListModel {" in source
    assert "function _syncRows(flat, animate)" in source
    assert "treeRowModel.insert(" in source
    assert "treeRowModel.remove(" in source
    assert "model: control._rowModel" in source
    assert 'PropertyAction { property: "opacity"; value: 0 }' in source
    assert "PauseAnimation { duration: Enums.duration.ultraFast }" in source
    assert "displaced: Transition {" in source
    # 可编辑输入框必须把文字镜像进查询，且收起后丢弃查询。
    assert "onTextEdited: function(text)" in source
    assert "onPopupVisibleChanged:" in source
