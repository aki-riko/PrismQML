# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""DateTimePicker visual stacking regressions. 日期时间选择器视觉层级回归。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "date-time-picker-visual-regression.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property int expectedBaseZ: Enums.zIndex.base
    readonly property int expectedContentZ: Enums.zIndex.content

    width: 700
    height: 400

    DateTimePicker {
        objectName: "picker"
        width: 520
        type: Enums.picker.type_datetime
        year: 2026
        month: 7
        day: 18
        hour: 15
        minute: 10
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


def _descendants(root: QObject) -> list[QObject]:
    result = []
    pending = list(root.children())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.children())
    return result


def _new_visible_windows(windows_before):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
    ]


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
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    picker = root.findChild(QObject, "picker")
    assert picker is not None
    return engine, component, root, picker, warnings


def _popup_parts(picker):
    popup_content = next(
        child
        for child in _descendants(picker)
        if all(
            child.metaObject().indexOfProperty(name) >= 0
            for name in ("col2Loader", "col3Loader", "hourWheelLoader")
        )
    )
    wheel_area = next(
        child
        for child in _descendants(popup_content)
        if child.metaObject().indexOfProperty("_wheelWidth") >= 0
    )
    row = next(
        child
        for child in wheel_area.childItems()
        if child.metaObject().className().startswith("QQuickRow")
    )
    highlight = next(
        child
        for child in wheel_area.childItems()
        if child.metaObject().className().startswith("QQuickRectangle")
    )
    loaders = [
        child
        for child in row.childItems()
        if child.metaObject().className().startswith("QQuickLoader")
        and child.property("active")
    ]
    return row, highlight, loaders


def test_selected_row_text_stays_above_opaque_highlight(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, picker, warnings = _create_scene()
    try:
        picker.openPopup()
        assert _wait_for(lambda: picker.property("isOpen"))
        assert _wait_for(lambda: picker.property("_tempYear") == 2026)
        row, highlight, loaders = _popup_parts(picker)

        assert highlight.property("z") == root.property("expectedBaseZ")
        assert row.property("z") == root.property("expectedContentZ")
        assert row.property("z") > highlight.property("z")

        assert len(loaders) == 5
        expected_date_indices = [100, 6, 17] if picker.property("_yearFirst") else [6, 17, 100]
        expected_indices = [*expected_date_indices, 15, 10]
        assert _wait_for(
            lambda: [
                loader.property("item").property("currentIndex")
                for loader in loaders
            ]
            == expected_indices
        )
        assert warnings == []
    finally:
        picker.closePopup()
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        _pump()
        assert _new_visible_windows(windows_before) == []
