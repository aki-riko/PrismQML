# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Calendar core runtime contracts. 日历核心运行时合同。"""

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


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "calendar-picker-core-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 420
    height: 420
    visible: true

    CalendarPickerCore {
        id: calendar
        objectName: "calendar"
        x: 50
        y: 30
        width: 256
        year: 2026
        month: 4
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


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def _day_cells(calendar: QQuickItem) -> list[QQuickItem]:
    return [
        child
        for child in _visual_descendants(calendar)
        if child.metaObject().indexOfProperty("cellDate") >= 0
        and child.metaObject().indexOfProperty("displayDay") >= 0
        and child.metaObject().indexOfProperty("isCurrent") >= 0
    ]


def _current_cell(calendar: QQuickItem, day: int) -> QQuickItem:
    matches = [
        cell
        for cell in _day_cells(calendar)
        if cell.property("isCurrent") and cell.property("displayDay") == day
    ]
    assert len(matches) == 1
    return matches[0]


def _previous_month_cell(calendar: QQuickItem) -> QQuickItem:
    matches = [cell for cell in _day_cells(calendar) if cell.property("isPrevMonth")]
    assert matches
    return matches[0]


def _point_for(window: QQuickWindow, item: QQuickItem) -> QPoint:
    point = item.mapToItem(
        window.contentItem(), QPointF(item.width() / 2, item.height() / 2)
    )
    return QPoint(round(point.x()), round(point.y()))


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
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
    calendar = window.findChild(QQuickItem, "calendar")
    assert calendar is not None
    assert _wait_for(lambda: len(_day_cells(calendar)) == 42)
    return engine, component, window, calendar, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def _assert_current_day_click(window, calendar) -> None:
    days = []
    dates = []
    calendar.dayClicked.connect(days.append)
    calendar.dateChanged.connect(lambda year, month, day: dates.append((year, month, day)))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _point_for(window, _current_cell(calendar, 15)),
    )
    assert calendar.property("day") == 15
    assert days == [15]
    assert dates == [(2026, 4, 15)]


def _assert_cross_year_navigation(calendar) -> None:
    calendar.setDate(2026, 1, 9)
    assert calendar.property("year") == 2026
    assert calendar.property("month") == 1
    assert calendar.property("day") == 9
    calendar.prevMonth()
    assert calendar.property("_animating")
    calendar.nextMonth()
    assert _wait_for(lambda: not calendar.property("_animating"))
    assert (calendar.property("year"), calendar.property("month")) == (2025, 12)
    calendar.nextMonth()
    assert _wait_for(lambda: not calendar.property("_animating"))
    assert (calendar.property("year"), calendar.property("month")) == (2026, 1)


def test_calendar_core_current_day_and_cross_year_navigation(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, calendar, warnings = _create_scene()
    try:
        _assert_current_day_click(window, calendar)
        _assert_cross_year_navigation(calendar)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_calendar_core_adjacent_day_emits_target_month(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, calendar, warnings = _create_scene()
    try:
        dates = []
        calendar.dateChanged.connect(
            lambda year, month, day: dates.append((year, month, day))
        )
        previous_cell = _previous_month_cell(calendar)
        target_day = previous_cell.property("displayDay")
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            _point_for(window, previous_cell),
        )
        assert dates == [(2026, 3, target_day)]
        assert _wait_for(lambda: not calendar.property("_animating"))
        assert (calendar.property("year"), calendar.property("month")) == (2026, 3)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
