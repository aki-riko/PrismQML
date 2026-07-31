# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Calendar picker convention regressions. 日历选择器规范回归。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QEventLoop,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    QTimer,
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
    / "DatePicker"
    / "CalendarPicker.qml"
)
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
    readonly property int singleWidth: Enums.controlSize.calendarPickerWidth
    readonly property int rangeWidth: Enums.controlSize.calendarPickerRangeWidth
    readonly property real visibleOpacity: Enums.opacityLevel.visible
    readonly property real secondaryOpacity: Enums.opacityLevel.secondary
    readonly property int slideDownAnimation:
        Enums.calendarPicker.popupAnimationSlideDown

    width: 520
    height: 100
    Component.onCompleted: Translator.setLanguage(Enums.lang.zh_CN)

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

HOVER_SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 520
    height: 320
    visible: true

    CalendarPicker {
        id: picker
        objectName: "picker"
        x: 40
        y: 40
        year: 2026
        month: 3
        day: 4
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


def _calendar_view(picker):
    matches = [
        child
        for child in _descendants(picker)
        if child.metaObject().className().startswith("CalendarPickerCore")
    ]
    assert len(matches) == 1, [child.metaObject().className() for child in matches]
    return matches[0]


def _create_hover_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(HOVER_SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    picker = window.findChild(QQuickItem, "picker")
    assert picker is not None
    assert _wait_for(window.isExposed)
    return engine, component, window, picker, warnings


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
    assert picker.property("implicitWidth") == calendar_scene.property("singleWidth")
    assert picker.property("implicitHeight") == calendar_scene.property("inputHeight")
    assert picker.property("displayDate") == "2026-03-04"
    assert icon.property("opacity") == calendar_scene.property("visibleOpacity")
    assert popup.property("animationType") == calendar_scene.property("slideDownAnimation")
    assert popup.property("popupWidth") == calendar_scene.property("popupWidth")
    assert QMetaObject.invokeMethod(picker, "reset")
    _pump()
    assert not picker.property("hasDate")
    assert picker.property("displayDate") == "选择日期"
    assert icon.property("opacity") == calendar_scene.property("secondaryOpacity")


def test_calendar_picker_range_runtime_contract(calendar_scene):
    picker = calendar_scene.findChild(QObject, "range")
    icon = _calendar_icon(calendar_scene, picker)
    assert picker.property("implicitWidth") == calendar_scene.property("rangeWidth")
    assert picker.property("displayDate") == "2026-01-02 ~ 2026-03-04"
    assert picker.property("weekDays").toVariant() == [
        "日", "一", "二", "三", "四", "五", "六"
    ]
    assert picker.property("monthFormat") == "{year}年{month}月"
    assert icon.property("opacity") == calendar_scene.property("visibleOpacity")
    assert QMetaObject.invokeMethod(picker, "reset")
    _pump()
    assert not picker.property("hasRange")
    assert picker.property("displayDate") == "选择日期范围"
    assert icon.property("opacity") == calendar_scene.property("secondaryOpacity")


def test_calendar_picker_cold_open_loads_and_syncs_popup(calendar_scene):
    picker = calendar_scene.findChild(QObject, "single")
    popup = _calendar_popup(picker)
    assert not picker.property("_popupContentRequested")
    assert not any(
        child.metaObject().className().startswith("CalendarPickerCore")
        for child in _descendants(picker)
    )

    assert QMetaObject.invokeMethod(picker, "openPopup")
    assert _wait_for(lambda: picker.property("isOpen"))
    view = _calendar_view(picker)
    assert (view.property("year"), view.property("month"), view.property("day")) == (
        2026,
        3,
        4,
    )
    assert not view.property("rangeMode")
    assert QMetaObject.invokeMethod(picker, "closePopup")
    assert _wait_for(
        lambda: not picker.property("isOpen")
        and not popup.property("isOpen")
        and not popup.property("isClosing")
    )


def test_calendar_picker_hover_prewarms_without_opening(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, picker, warnings = _create_hover_scene()
    try:
        popup = _calendar_popup(picker)
        assert not picker.property("_popupContentRequested")
        assert not any(
            child.metaObject().className().startswith("CalendarPickerCore")
            for child in _descendants(picker)
        )

        QTest.mouseMove(window, QPoint(window.width() - 12, window.height() - 12))
        _pump()
        point = picker.mapToItem(
            window.contentItem(), QPointF(picker.width() / 2, picker.height() / 2)
        )
        QTest.mouseMove(window, point.toPoint())

        assert _wait_for(lambda: picker.property("_popupContentRequested"))
        assert _wait_for(lambda: popup.property("_prewarmed"))
        _calendar_view(picker)
        assert not picker.property("isOpen")
        assert not popup.property("isOpen")
        assert [
            item
            for item in QGuiApplication.topLevelWindows()
            if item.isVisible()
            and item is not window
            and not any(item is existing for existing in windows_before)
        ] == []
        assert warnings == []
    finally:
        picker.closePopup()
        window.close()
        window.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump()
        assert [
            item
            for item in QGuiApplication.topLevelWindows()
            if item.isVisible()
            and not any(item is existing for existing in windows_before)
        ] == []


def test_calendar_picker_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        item for item in violations if item.rule in {"QML008", "QML009"}
    ] == []


def test_calendar_picker_uses_enum_tokens():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert "Enums.controlSize.calendarPickerWidth" in source
    assert "Enums.controlSize.calendarPickerRangeWidth" in source
    assert "Enums.calendarPicker.popupAnimationSlideDown" in source
    assert "Enums.calendarPicker.monthMinimum" in source
    assert "Enums.calendarPicker.monthMaximum" in source
    assert "Enums.calendarPicker.dayMinimum" in source
    assert "Enums.calendarPicker.dayMaximum" in source
    assert "Enums.calendarPicker.dateFieldWidth" in source
    assert "Enums.calendarPicker.dateSeparator" in source
    assert "Enums.calendarPicker.rangeSeparator" in source
    assert "Enums.opacityLevel.visible" in source
    assert "Enums.opacityLevel.secondary" in source
