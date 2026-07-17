# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Calendar picker convention regressions. 日历选择器规范回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QMetaObject, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "calendar-picker-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property string calendarIcon: Enums.icon.calendar
    readonly property int inputHeight: Enums.controlSize.inputHeight
    readonly property int popupWidth: Enums.controlSize.calendarPopupWidth

    width: 520
    height: 100

    CalendarPicker {
        objectName: "single"
        year: 2026
        month: 3
        day: 4
    }

    CalendarPicker {
        objectName: "range"
        x: 240
        type: Enums.calendarPicker.type_range
        startDate: new Date(2026, 0, 2)
        endDate: new Date(2026, 2, 4)
        hasRange: true
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


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
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump()
    return engine, component, root, warnings


def _descendants(root):
    result = []
    pending = list(root.children())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.children())
    return result


def _find_unique(root, predicate):
    matches = [child for child in _descendants(root) if predicate(child)]
    assert len(matches) == 1, [child.metaObject().className() for child in matches]
    return matches[0]


def _calendar_icon(root, picker):
    return _find_unique(
        picker,
        lambda child: child.metaObject().indexOfProperty("icon") >= 0
        and child.property("icon") == root.property("calendarIcon"),
    )


def _calendar_popup(picker):
    return _find_unique(
        picker,
        lambda child: child.metaObject().indexOfProperty("popupWidth") >= 0
        and child.metaObject().indexOfProperty("animationType") >= 0,
    )


@pytest.fixture
def calendar_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene()
    try:
        yield root
        assert warnings == []
        assert [
            window for window in QGuiApplication.topLevelWindows()
            if window.isVisible()
            and not any(window is existing for existing in windows_before)
        ] == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_calendar_picker_single_runtime_contract(calendar_scene):
    picker = calendar_scene.findChild(QObject, "single")
    icon = _calendar_icon(calendar_scene, picker)
    popup = _calendar_popup(picker)
    assert picker.property("implicitWidth") == 180
    assert picker.property("implicitHeight") == calendar_scene.property("inputHeight")
    assert picker.property("displayDate") == "2026-03-04"
    assert icon.property("opacity") == pytest.approx(1.0)
    assert popup.property("animationType") == 1
    assert popup.property("popupWidth") == calendar_scene.property("popupWidth")
    assert QMetaObject.invokeMethod(picker, "reset")
    _pump()
    assert not picker.property("hasDate")
    assert picker.property("displayDate") == "选择日期"
    assert icon.property("opacity") == pytest.approx(0.6)


def test_calendar_picker_range_runtime_contract(calendar_scene):
    picker = calendar_scene.findChild(QObject, "range")
    icon = _calendar_icon(calendar_scene, picker)
    assert picker.property("implicitWidth") == 220
    assert picker.property("displayDate") == "2026-01-02 ~ 2026-03-04"
    assert picker.property("weekDays").toVariant() == [
        "日", "一", "二", "三", "四", "五", "六"
    ]
    assert picker.property("monthFormat") == "{month}月 {year}"
    assert icon.property("opacity") == pytest.approx(1.0)
    assert QMetaObject.invokeMethod(picker, "reset")
    _pump()
    assert not picker.property("hasRange")
    assert picker.property("displayDate") == "选择日期范围"
    assert icon.property("opacity") == pytest.approx(0.6)
