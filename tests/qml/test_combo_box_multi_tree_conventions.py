# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Multi-tree combo parent-chain regressions. 多选树下拉框父链回归。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
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
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "ComboBox"
    / "ComboBoxMultiTree.qml"
)
CONTENT_SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "ComboBox"
    / "_internal"
    / "ComboBoxMultiTreeContent.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "combo-box-multi-tree-conventions.qml")
)
SCENE_SOURCE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    // 弹层高度按内容算（与单树同口径）：行数 × 行高 + 搜索框，且不超过上限。
    // 旧实现写死 treePopupHeight，所以永远拉满、没有高度动画。
    readonly property int expectedRowHeight: Enums.comboBoxMetrics.itemHeight
    readonly property int expectedSearchHeight: Enums.comboBoxMetrics.searchBoxHeight
    readonly property int expectedPopupMaxHeight: Enums.comboBoxMetrics.treePopupHeight
    readonly property int expectedPopupMinWidth: Enums.comboBoxMetrics.treePopupMinWidth
    readonly property int expectedContentPadding: Enums.spacing.xs
    readonly property int expectedPanelOffset: Enums.popupMetrics.panelOffset

    function popupHeightFor(rows) {
        // popupHeight = 内容视口（行 + 搜索框）+ 2 × 弹层内边距，且不超过上限
        return Math.min(rows * expectedRowHeight + expectedSearchHeight,
                        expectedPopupMaxHeight) + 2 * expectedContentPadding
    }

    width: 560
    height: 280
    visible: true

    ComboBoxMultiTree {
        id: combo
        objectName: "combo"
        x: 70
        y: 60
        width: 220
        placeholderText: "Choose leaves"
        model: [
            {
                "text": "Parent",
                "children": [
                    {"text": "Leaf A"},
                    {"text": "Leaf B"}
                ]
            },
            {"text": "Solo"}
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
    return predicate()


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _flat_model(combo: QQuickItem) -> QObject:
    matches = [
        child
        for child in combo.findChildren(QObject)
        if "QQmlListModel" in child.metaObject().className()
        and child.metaObject().indexOfProperty("count") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _popup_core(combo: QQuickItem) -> QQuickItem:
    matches = [
        child
        for child in combo.findChildren(QObject)
        if isinstance(child, QQuickItem)
        and child.metaObject().className().startswith("PopupWindowCore")
        and child.metaObject().indexOfProperty("popupWidth") >= 0
        and child.metaObject().indexOfProperty("isClosing") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _point_for(window: QQuickWindow, item: QQuickItem) -> QPoint:
    point = item.mapToItem(
        window.contentItem(), QPointF(item.width() / 2, item.height() / 2)
    )
    return QPoint(round(point.x()), round(point.y()))


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE.encode("utf-8"), SCENE_URL)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isActive)
    combo = window.findChild(QQuickItem, "combo")
    assert combo is not None
    flat_model = _flat_model(combo)
    assert _wait_for(lambda: flat_model.property("count") == 4)
    return engine, component, window, combo, flat_model, warnings


def _row_items(popup_window: QQuickWindow) -> list:
    """弹层里的树行委托（按 hasChildren/depth 两个属性识别），按纵向位置排序。"""
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


def _dispose_scene(engine, component, window, combo) -> None:
    if combo.property("isOpen"):
        combo.closePopup()
        _wait_for(lambda: not combo.property("isOpen"))
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def test_combo_box_multi_tree_selection_search_and_popup_lifecycle(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, combo, flat_model, warnings = _create_scene()
    try:
        selections = []
        combo.selectionChanged.connect(lambda paths: selections.append(_variant(paths)))
        parent = combo._findNodeByPath(["Parent"])
        assert combo._getSelectionState(parent, ["Parent"]) == 0

        combo._toggleExpand("root_0")
        assert _wait_for(lambda: flat_model.property("count") == 2)
        combo.setProperty("_searchText", "LEAF B")
        assert _wait_for(lambda: flat_model.property("count") == 1)
        combo.setProperty("_searchText", "")
        assert _wait_for(lambda: flat_model.property("count") == 2)
        combo._toggleExpand("root_0")
        assert _wait_for(lambda: flat_model.property("count") == 4)

        combo._toggleSelection(["Parent"])
        _pump()
        assert _variant(combo.property("selectedPaths")) == [
            ["Parent", "Leaf A"],
            ["Parent", "Leaf B"],
        ]
        assert combo._getSelectionState(parent, ["Parent"]) == 2
        assert combo.property("displayText") == "Leaf A, Leaf B"

        combo._toggleSelection(["Parent", "Leaf A"])
        _pump()
        assert _variant(combo.property("selectedPaths")) == [["Parent", "Leaf B"]]
        assert combo._getSelectionState(parent, ["Parent"]) == 1
        assert combo.property("displayText") == "Leaf B"
        assert selections[-1] == [["Parent", "Leaf B"]]

        combo.setProperty("_searchText", "leaf b")
        assert _wait_for(lambda: flat_model.property("count") == 2)

        popup = _popup_core(combo)
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            _point_for(window, combo),
        )
        assert _wait_for(lambda: combo.property("isOpen"))
        assert popup.property("popupWidth") == max(
            combo.width(), window.property("expectedPopupMinWidth")
        )
        # 打开时查询被清空（openPopup 的既有口径），所以是 4 行全量；
        # 弹层高度按内容算 = 行数 × 行高 + 搜索框，且不超过上限。
        expected_rows = flat_model.property("count")
        assert expected_rows == 4
        assert combo.property("_searchText") == ""
        expected_height = window.popupHeightFor(expected_rows)
        assert _wait_for(lambda: popup.property("popupHeight") == expected_height), (
            f"弹层高度没有收敛到按内容的 {expected_height}，实际 {popup.property('popupHeight')}"
        )
        assert _wait_for(lambda: len(_new_visible_windows(windows_before, window)) == 1)
        assert _wait_for(lambda: popup.property("isOpen"))
        popup_window = _new_visible_windows(windows_before, window)[0]
        target_global = window.mapToGlobal(combo.mapToScene(QPointF()).toPoint())
        assert popup_window.x() + window.property(
            "expectedPanelOffset"
        ) == target_global.x()

        combo.closePopup()
        assert _wait_for(lambda: not combo.property("isOpen"))
        assert _wait_for(lambda: not popup.property("isClosing"))
        closed_without_windows = _wait_for(
            lambda: _new_visible_windows(windows_before, window) == []
        )
        remaining_windows = _new_visible_windows(windows_before, window)
        assert closed_without_windows, [
            (
                item.metaObject().className(),
                item.objectName(),
                item.title(),
                item.isVisible(),
            )
            for item in remaining_windows
        ]
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window, combo)
        assert _new_visible_windows(windows_before) == []


def test_combo_box_multi_tree_fast_close_during_popup_startup(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, combo, _flat_model, warnings = _create_scene()
    try:
        popup = _popup_core(combo)
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            _point_for(window, combo),
        )
        assert combo.property("isOpen")
        assert not popup.property("isOpen")
        assert len(_new_visible_windows(windows_before, window)) == 1

        combo.closePopup()
        assert not combo.property("isOpen")
        assert _wait_for(lambda: not popup.property("isClosing"))
        assert _wait_for(lambda: _new_visible_windows(windows_before, window) == [])
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window, combo)
        assert _new_visible_windows(windows_before) == []


def test_combo_box_multi_tree_expanding_parent_animates_rows(qapp):
    """展开分类：新行先透明再淡入、下方行经过中间位置（与单树同一口径）。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, combo, flat_model, warnings = _create_scene()
    try:
        combo._toggleExpand("root_0")
        assert _wait_for(lambda: flat_model.property("count") == 2)

        popup = _popup_core(combo)
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            _point_for(window, combo),
        )
        assert _wait_for(lambda: combo.property("isOpen"))
        assert _wait_for(lambda: len(_new_visible_windows(windows_before, window)) == 1)
        popup_window = _new_visible_windows(windows_before, window)[0]
        _pump(160)

        def row_by_text(text):
            for item in _row_items(popup_window):
                if item.property("text") == text:
                    return item
            return None

        row_height = window.property("expectedRowHeight")
        tail_before = row_by_text("Solo")
        assert tail_before is not None
        before_y = tail_before.mapToScene(QPointF(0, 0)).y()

        combo._toggleExpand("root_0")

        min_opacity = 1.0
        moved = []
        for _ in range(14):
            _pump()
            new_row = row_by_text("Leaf A")
            if new_row is not None:
                min_opacity = min(min_opacity, new_row.opacity())
            tail = row_by_text("Solo")
            if tail is not None:
                moved.append(tail.mapToScene(QPointF(0, 0)).y())

        final_y = before_y + 2 * row_height
        assert min_opacity <= 0.05, (
            f"多选树新行首帧必须透明（否则与让位中的旧行文字重影），实测 {min_opacity}"
        )
        assert moved, "下方的行在动画期间不可见"
        assert any(before_y + 0.5 < y < final_y - 0.5 for y in moved), (
            f"多选树让位没有经过中间位置：起点 {before_y}、终点 {final_y}、采样 {moved}"
        )
        assert abs(moved[-1] - final_y) < 0.5
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window, combo)
        assert _new_visible_windows(windows_before) == []


def test_combo_box_multi_tree_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    content_source = CONTENT_SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    content_path = PurePosixPath(CONTENT_SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path) + scan_source_text(
        content_source, content_path
    )
    assert "interactive: false" in content_source
    assert (
        "PopupSmoothScroll {" in content_source
        and "flickable: treeListView" in content_source
        and "enabled: treeContainer.needsScroll" in content_source
    )
    assert 'var searchText = _searchText.toLowerCase()' in source
    assert source.count("_searchText.toLowerCase()") == 1
    # Traversal moved to ComboBoxTreeNodes.js; selection state stays here.
    # 遍历已移入 ComboBoxTreeNodes.js；选中语义仍留在本控件。
    assert 'import "_internal/ComboBoxTreeNodes.js" as TreeNodes' in source
    assert "TreeNodes.flatten(" in source
    assert "TreeNodes.expandAll(" in source
    assert "TreeNodes.toggleExpanded(" in source
    assert "function _hasMatchingDescendants(" not in source
    assert "function _collectExpandableNodes(" not in source
    assert "function _flattenTree(" not in source
    assert "control._getSelectionState(row.node, row.path)" in source
    assert "if (_safeSelectedPaths.length === 0) return 0" in source
    # 行增量同步与高度算术都在共用件里（与单树同一套）
    assert 'import "_internal/ComboBoxTreeRows.js" as TreeRows' in source
    assert 'TreeRows.syncRows(_flatListModel, rows, "nodeId", animate)' in source
    assert 'id: multiTreeSizer' in source
    assert "TreePopupSizer {" in source
    # 展开/收起过渡：先让位、新行再淡入（顺序不能反，否则文字重影）
    assert 'PropertyAction { property: "opacity"; value: 0 }' in content_source
    assert "PauseAnimation { duration: Enums.duration.ultraFast }" in content_source
    assert "displaced: Transition {" in content_source
    # 打开即聚焦弹层搜索框（弹层窗口懒创建，必须允许下一拍重试）
    assert "function _focusPopupSearch()" in source
    assert "_searchBox.focusInput()" in source
    assert "Qt.callLater(_focusPopupSearch)" in source
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
