# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Tree combo runtime contracts. 树形下拉框运行时合同。"""

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
    / "ComboBoxTree.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "combo-box-tree-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property int expectedItemHeight: Enums.comboBoxMetrics.itemHeight
    readonly property int expectedSearchHeight: Enums.comboBoxMetrics.searchBoxHeight
    readonly property int expectedSpacing: Enums.spacing.m
    readonly property int expectedMaxHeight: Enums.comboBoxMetrics.treePopupHeight
    readonly property int expectedPopupMinWidth: Enums.comboBoxMetrics.treePopupMinWidth
    readonly property int expectedPanelOffset: Enums.popupMetrics.panelOffset

    width: 560
    height: 280
    visible: true

    ComboBoxTree {
        id: combo
        objectName: "combo"
        x: 70
        y: 60
        width: 240
        model: [
            {
                "text": "Parent",
                "children": [
                    {"text": "Leaf A"},
                    {
                        "text": "Branch",
                        "children": [{"text": "Leaf B"}]
                    }
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


def _flat_model(combo: QQuickItem):
    return _variant(combo.property("_flatModel"))


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
    assert _wait_for(lambda: len(_flat_model(combo)) == 5)
    return engine, component, window, combo, warnings


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


def _assert_expand_and_search(combo: QQuickItem) -> None:
    assert [item["text"] for item in _flat_model(combo)] == [
        "Parent",
        "Leaf A",
        "Branch",
        "Leaf B",
        "Solo",
    ]
    combo._toggleExpand("root_0")
    assert _wait_for(lambda: len(_flat_model(combo)) == 2)
    assert [item["text"] for item in _flat_model(combo)] == ["Parent", "Solo"]
    combo._toggleExpand("root_0")
    assert _wait_for(lambda: len(_flat_model(combo)) == 5)
    combo.setProperty("_searchText", "leaf b")
    assert _wait_for(lambda: len(_flat_model(combo)) == 3)
    assert [item["text"] for item in _flat_model(combo)] == [
        "Parent",
        "Branch",
        "Leaf B",
    ]
    combo.setProperty("_searchText", "")
    assert _wait_for(lambda: len(_flat_model(combo)) == 5)


def _open_popup(window, combo, windows_before) -> QQuickItem:
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
    expected_height = min(
        len(_flat_model(combo)) * window.property("expectedItemHeight")
        + window.property("expectedSearchHeight")
        + window.property("expectedSpacing"),
        window.property("expectedMaxHeight"),
    )
    assert popup.property("popupHeight") == expected_height
    assert _wait_for(lambda: popup.property("isOpen"))
    assert _wait_for(lambda: len(_new_visible_windows(windows_before, window)) == 1)
    popup_window = _new_visible_windows(windows_before, window)[0]
    target_global = window.mapToGlobal(combo.mapToScene(QPointF()).toPoint())
    assert popup_window.x() + window.property(
        "expectedPanelOffset"
    ) == target_global.x()
    return popup


def _assert_path_selection(combo, popup, windows_before, window, selected) -> None:
    combo._selectNode("Leaf B", ["Parent", "Branch", "Leaf B"])
    assert combo.property("currentText") == "Parent → Branch → Leaf B"
    assert selected == [("Leaf B", ["Parent", "Branch", "Leaf B"])]
    assert _wait_for(lambda: not combo.property("isOpen"))
    assert _wait_for(lambda: not popup.property("isClosing"))
    assert _wait_for(lambda: _new_visible_windows(windows_before, window) == [])
    combo.setProperty("showPathFromRoot", False)
    combo._selectNode("Leaf A", ["Parent", "Leaf A"])
    assert combo.property("currentText") == "Leaf A"
    assert selected[-1] == ("Leaf A", ["Parent", "Leaf A"])


def test_combo_box_tree_expand_search_select_and_popup_lifecycle(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, combo, warnings = _create_scene()
    try:
        selected = []
        combo.itemSelected.connect(
            lambda text, path: selected.append((text, _variant(path)))
        )
        _assert_expand_and_search(combo)
        popup = _open_popup(window, combo, windows_before)
        _assert_path_selection(combo, popup, windows_before, window, selected)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window, combo)
        assert _new_visible_windows(windows_before) == []


def test_combo_box_tree_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []


def test_combo_box_tree_fast_close_during_popup_startup(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, combo, warnings = _create_scene()
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
