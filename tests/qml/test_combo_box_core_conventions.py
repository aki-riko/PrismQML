# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ComboBoxCore public and interaction contracts. 下拉框核心公共与交互合同。"""

from pathlib import Path, PurePosixPath

import pytest
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
from PySide6.QtGui import QGuiApplication, QWheelEvent
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
    / "ComboBoxCore.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "combo-box-core-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property int expectedPopupPadding: Enums.comboBoxMetrics.popupPadding

    width: 720
    height: 360
    visible: true

    ComboBoxCore {
        id: combo
        objectName: "combo"
        x: 60
        y: 60
        width: 260
        model: [
            {"text": "Alpha", "data": 10, "icon": "alpha-icon"},
            {"text": "Beta", "data": 20, "icon": "beta-icon", "enabled": false},
            {"text": "Gamma", "data": 30, "icon": "gamma-icon"}
        ]
        currentIndex: 0
        maxVisibleItems: 3
        popupItemHeight: 40
    }

    ComboBoxCore {
        id: editableCombo
        objectName: "editableCombo"
        x: 380
        y: 60
        width: 260
        model: ["Alpha", "Beta", "Gamma"]
        currentIndex: 0
        editable: true
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1800) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _object_descendants(root: QObject) -> list[QObject]:
    result = []
    pending = list(root.children())
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.children())
    return result


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.childItems())
    return result


def _popup_core(combo: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in _object_descendants(combo)
        if isinstance(item, QQuickItem)
        and item.metaObject().className().startswith("PopupWindowCore")
        and item.metaObject().indexOfProperty("isClosing") >= 0
    ]
    assert len(matches) == 1
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


def _local_point(window: QQuickWindow, item: QQuickItem, x: float, y: float):
    point = item.mapToItem(window.contentItem(), QPointF(x, y))
    return QPoint(round(point.x()), round(point.y()))


def _popup_rows(popup_window: QQuickWindow) -> list[QQuickItem]:
    rows = [
        item
        for item in _visual_descendants(popup_window.contentItem())
        if item.metaObject().indexOfProperty("itemEnabled") >= 0
        and item.metaObject().indexOfProperty("selected") >= 0
        and item.metaObject().indexOfProperty("text") >= 0
    ]
    return sorted(
        rows,
        key=lambda item: item.mapToItem(popup_window.contentItem(), 0, 0).y(),
    )


def _send_wheel(window: QQuickWindow, point: QPoint, delta: int) -> None:
    event = QWheelEvent(
        QPointF(point),
        QPointF(window.mapToGlobal(point)),
        QPoint(),
        QPoint(0, delta),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    QCoreApplication.sendEvent(window, event)
    _pump()


def _type_custom(window: QQuickWindow) -> None:
    QTest.keyClick(window, Qt.Key.Key_C, Qt.KeyboardModifier.ShiftModifier)
    for key in (
        Qt.Key.Key_U,
        Qt.Key.Key_S,
        Qt.Key.Key_T,
        Qt.Key.Key_O,
        Qt.Key.Key_M,
    ):
        QTest.keyClick(window, key)


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
    editable = window.findChild(QQuickItem, "editableCombo")
    assert combo is not None and editable is not None
    return engine, component, window, combo, editable, warnings


def _close_combo(combo: QQuickItem) -> None:
    popup = _popup_core(combo)
    if combo.property("isOpen"):
        combo.closePopup()
    _wait_for(lambda: not combo.property("isOpen"))
    _wait_for(lambda: not popup.property("isClosing"))


def _dispose_scene(engine, component, window, combo, editable) -> None:
    _close_combo(combo)
    _close_combo(editable)
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def _open_popup(window, combo, windows_before):
    popup = _popup_core(combo)
    click_point = _local_point(window, combo, combo.width() - 12, combo.height() / 2)
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=click_point)
    assert _wait_for(lambda: combo.property("isOpen"))
    assert _wait_for(lambda: popup.property("isOpen"))
    assert _wait_for(lambda: abs(popup.property("_scale") - 1.0) < 0.001)
    assert _wait_for(
        lambda: popup.property("_clipHeight") == popup.property("popupHeight")
    )
    popup_windows = _new_visible_windows(windows_before, window)
    assert len(popup_windows) == 1
    popup_window = popup_windows[0]
    assert isinstance(popup_window, QQuickWindow)
    popup_window.requestActivate()
    assert _wait_for(popup_window.isActive)
    return popup, popup_window


def test_combo_box_core_qt_style_item_methods_preserve_metadata(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, component, window, combo, editable, warnings = scene
    try:
        assert combo.count() == 3
        assert combo.itemText(1) == "Beta"
        assert combo.findText("Beta") == 1
        assert combo.currentData() == 10
        assert combo.itemData(1) == 20
        assert combo.itemIcon(1) == "beta-icon"
        assert not combo.isItemEnabled(1)

        combo.setCurrentText("Gamma")
        assert combo.property("currentIndex") == 2
        assert combo.property("currentText") == "Gamma"
        combo.setItemText(2, "Gamma Renamed")
        assert combo.itemText(2) == "Gamma Renamed"
        assert combo.property("currentText") == "Gamma Renamed"
        combo.setProperty("currentIndex", 0)

        combo.addItem("Delta", 40)
        assert combo.count() == 4
        assert combo.itemData(3) == 40
        combo.setItemData(0, 11)
        combo.insertItem(1, "Inserted", 15)
        assert combo.itemText(1) == "Inserted"
        assert combo.itemData(0) == 11
        assert combo.itemData(1) == 15
        assert combo.itemData(2) == 20

        combo.setItemIcon(1, "inserted-icon")
        combo.setItemEnabled(1, False)
        assert combo.itemIcon(1) == "inserted-icon"
        assert not combo.isItemEnabled(1)
        combo.removeItem(0)
        assert combo.itemText(0) == "Inserted"
        assert combo.itemData(0) == 15
        assert combo.itemIcon(0) == "inserted-icon"
        assert not combo.isItemEnabled(0)

        combo.clear()
        combo.addItem("Fresh", None)
        assert combo.itemData(0) is None
        assert combo.itemIcon(0) == ""
        assert combo.isItemEnabled(0)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window, combo, editable)
        assert _new_visible_windows(windows_before) == []


def test_combo_box_core_popup_honors_height_icon_disabled_and_signals(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, component, window, combo, editable, warnings = scene
    activated = []
    text_activated = []
    index_changed = []
    text_changed = []
    wheel_scrolled = []
    combo.activated.connect(activated.append)
    combo.textActivated.connect(text_activated.append)
    combo.indexChanged.connect(index_changed.append)
    combo.textChanged.connect(text_changed.append)
    combo.wheelScrolled.connect(wheel_scrolled.append)
    try:
        popup = _popup_core(combo)
        hover_point = _local_point(
            window, combo, combo.width() - 12, combo.height() / 2
        )
        QTest.mouseMove(window, hover_point)
        assert _wait_for(lambda: popup.property("_prewarmed"))
        assert _new_visible_windows(windows_before, window) == []

        _send_wheel(window, hover_point, 120)
        assert wheel_scrolled == [120]
        popup, popup_window = _open_popup(window, combo, windows_before)
        expected_height = 3 * combo.property("popupItemHeight") + window.property(
            "expectedPopupPadding"
        )
        rows = _popup_rows(popup_window)
        assert len(rows) == 3
        assert [row.property("itemEnabled") for row in rows] == [True, False, True]
        assert [row.property("icon") for row in rows] == [
            "alpha-icon",
            "beta-icon",
            "gamma-icon",
        ]
        assert [row.height() for row in rows] == [40, 40, 40]
        assert popup.property("popupHeight") == expected_height

        QTest.mouseClick(popup_window, Qt.MouseButton.LeftButton, pos=_point_for(popup_window, rows[1]))
        _pump()
        assert combo.property("currentIndex") == 0
        assert combo.property("isOpen")

        QTest.mouseClick(popup_window, Qt.MouseButton.LeftButton, pos=_point_for(popup_window, rows[2]))
        assert _wait_for(lambda: not combo.property("isOpen"))
        assert combo.property("currentIndex") == 2
        assert combo.property("currentText") == "Gamma"
        assert activated == [2]
        assert text_activated == ["Gamma"]
        assert index_changed == [2]
        assert text_changed == ["Gamma"]
        assert warnings == []
        assert _wait_for(lambda: _new_visible_windows(windows_before, window) == [])
    finally:
        _dispose_scene(engine, component, window, combo, editable)
        assert _new_visible_windows(windows_before) == []


def test_combo_box_core_edit_then_select_restores_model_text(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, component, window, combo, editable, warnings = scene
    edited = []
    editable.textEdited.connect(edited.append)
    try:
        inputs = [
            item
            for item in _visual_descendants(editable)
            if item.metaObject().className().startswith("QQuickTextInput")
            and item.isVisible()
        ]
        assert len(inputs) == 1
        click_point = _local_point(window, editable, 40, editable.height() / 2)
        QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=click_point)
        QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        _type_custom(window)
        assert _wait_for(lambda: editable.property("currentText") == "custom"), (
            editable.property("currentText"),
            inputs[0].property("text"),
            inputs[0].property("activeFocus"),
            edited,
        )
        assert editable.property("currentIndex") == -1
        assert edited[-1] == "custom"

        editable.setProperty("model", ["Alpha", "Beta", "Gamma", "Delta"])
        _pump()
        assert editable.property("currentText") == "custom"
        assert inputs[0].property("text") == "custom"

        popup, popup_window = _open_popup(window, editable, windows_before)
        rows = _popup_rows(popup_window)
        assert len(rows) == 4
        QTest.mouseClick(popup_window, Qt.MouseButton.LeftButton, pos=_point_for(popup_window, rows[1]))
        assert _wait_for(lambda: not editable.property("isOpen"))
        assert editable.property("currentIndex") == 1
        assert editable.property("currentText") == "Beta"

        editable.setProperty("currentIndex", 2)
        assert _wait_for(lambda: editable.property("currentText") == "Gamma")
        assert warnings == []
        assert _wait_for(lambda: _new_visible_windows(windows_before, window) == [])
    finally:
        _dispose_scene(engine, component, window, combo, editable)
        assert _new_visible_windows(windows_before) == []


def test_combo_box_core_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
