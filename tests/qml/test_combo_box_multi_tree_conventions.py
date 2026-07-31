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
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "combo-box-multi-tree-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property int expectedPopupHeight: Enums.comboBoxMetrics.treePopupHeight
    readonly property int expectedPopupMinWidth: Enums.comboBoxMetrics.treePopupMinWidth
    readonly property int expectedPanelOffset: Enums.popupMetrics.panelOffset

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
    component.setData(SCENE_SOURCE, SCENE_URL)
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
        assert popup.property("popupHeight") == window.property("expectedPopupHeight")
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


def test_combo_box_multi_tree_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert "interactive: false" in source
    assert (
        "PopupSmoothScroll { flickable: treeListView; "
        "enabled: treeContainer.needsScroll }"
    ) in source
    assert 'var searchText = _searchText.toLowerCase()' in source
    assert source.count("_searchText.toLowerCase()") == 1
    assert "_hasMatchingDescendants(node.children, searchText)" in source
    assert "if (_safeSelectedPaths.length === 0) return 0" in source
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
