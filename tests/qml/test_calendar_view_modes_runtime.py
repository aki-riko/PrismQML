# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""CalendarView display modes, multi-selection, blackouts and today button.

CalendarView 显示模式、多选、禁用日期与今天按钮运行时合同。
"""

from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "calendar-view-modes.qml")
)

SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"
    width: 460
    height: 420
    visible: true

    property var dayClicks: []
    property var dateChanges: []
    property var rangeClicks: []

    readonly property int monthMode: Enums.calendarPicker.display_month
    readonly property int yearMode: Enums.calendarPicker.display_year
    readonly property int decadeMode: Enums.calendarPicker.display_decade
    readonly property int singleMode: Enums.calendarPicker.selection_single
    readonly property int multipleMode: Enums.calendarPicker.selection_multiple
    readonly property int rangeSelectionMode: Enums.calendarPicker.selection_range
    readonly property int todayYear: new Date().getFullYear()
    readonly property int todayMonth: new Date().getMonth() + 1
    readonly property int todayDay: new Date().getDate()

    CalendarPickerCore {
        id: calendar
        objectName: "calendar"
        x: 20
        y: 20
        width: 300
        height: 340
        year: 2026
        month: 3
        onDayClicked: (day) => root.dayClicks = root.dayClicks.concat([day])
        onDateChanged: (y, m, d) =>
            root.dateChanges = root.dateChanges.concat([y + "-" + m + "-" + d])
        onRangeDateClicked: (date) =>
            root.rangeClicks = root.rangeClicks.concat([date.toDateString()])
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1500) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
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
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    _pump(80)
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(1)


def _calendar(window) -> QQuickItem:
    item = window.findChild(QQuickItem, "calendar")
    assert item is not None
    return item


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _descendants(root: QQuickItem):
    result = []
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.childItems())
    return result


def _day_of(value) -> int:
    if hasattr(value, "date"):
        return value.date().day()
    return value.day()


def _day_cell(calendar, day: int) -> QQuickItem:
    matches = [
        child
        for child in _descendants(calendar)
        if child.metaObject().indexOfProperty("displayDay") >= 0
        and child.metaObject().indexOfProperty("isCurrent") >= 0
        and child.property("isCurrent") is True
        and child.property("displayDay") == day
    ]
    assert len(matches) == 1, [
        (child.property("displayDay"), child.property("isCurrent"))
        for child in _descendants(calendar)
        if child.metaObject().indexOfProperty("displayDay") >= 0
    ]
    return matches[0]


def _period_cells(period_grid: QQuickItem) -> list:
    cells = [
        child
        for child in _descendants(period_grid)
        if child.metaObject().indexOfProperty("_activePeriod") >= 0
    ]
    # _descendants walks child items with a stack, so restore the grid order
    # _descendants 使用栈遍历, 这里按网格顺序还原
    return sorted(cells, key=lambda cell: (round(cell.y()), round(cell.x())))


def _click(window: QQuickWindow, item: QQuickItem) -> None:
    centre = item.mapToItem(
        window.contentItem(), QPointF(item.width() / 2, item.height() / 2)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(centre.x()), round(centre.y())),
    )
    _pump(60)


def _invoke(item, name: str) -> None:
    assert QMetaObject.invokeMethod(item, name)
    _pump(40)


def test_defaults_keep_the_classic_month_grid(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        calendar = _calendar(window)
        assert calendar.property("displayMode") == window.property("monthMode")
        assert calendar.property("selectionMode") == window.property("singleMode")
        assert list(_variant(calendar.property("selectedDates"))) == []
        assert list(_variant(calendar.property("blackoutDates"))) == []
        assert calendar.property("showTodayButton") is False

        period_loader = calendar.findChild(QQuickItem, "calendarPeriodGridLoader")
        today_loader = calendar.findChild(QQuickItem, "calendarTodayLoader")
        assert period_loader is not None and today_loader is not None
        assert period_loader.property("active") is False
        assert today_loader.property("active") is False

        day_cells = [
            child
            for child in _descendants(calendar)
            if child.metaObject().indexOfProperty("displayDay") >= 0
        ]
        assert len(day_cells) == 42
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_year_and_decade_modes_are_selectable(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        calendar = _calendar(window)
        period_loader = calendar.findChild(QQuickItem, "calendarPeriodGridLoader")

        calendar.setProperty("displayMode", window.property("yearMode"))
        _pump(40)
        assert _wait_for(lambda: period_loader.property("active"))
        months = _period_cells(period_loader.property("item"))
        assert len(months) == 12

        # Choosing a month returns to the day grid 选择月份回到日期网格
        _click(window, months[4])
        assert calendar.property("month") == 5
        assert calendar.property("displayMode") == window.property("monthMode")
        assert _wait_for(lambda: not period_loader.property("active"))

        # Decade mode lists ten years and steps by ten 十年模式列出十个年份并按十步进
        calendar.setProperty("displayMode", window.property("decadeMode"))
        _pump(40)
        assert _wait_for(lambda: period_loader.property("active"))
        period_grid = period_loader.property("item")
        years = _period_cells(period_grid)
        assert len(years) == 10
        assert period_grid.property("_firstValue") == 2020

        _invoke(calendar, "nextPage")
        assert calendar.property("year") == 2036
        assert calendar.property("displayMode") == window.property("decadeMode")
        _invoke(calendar, "previousPage")
        assert calendar.property("year") == 2026

        _click(window, years[2])
        assert calendar.property("year") == 2022
        assert calendar.property("displayMode") == window.property("yearMode")
        _invoke(calendar, "previousPage")
        assert calendar.property("year") == 2021
        _invoke(calendar, "nextPage")
        assert calendar.property("year") == 2022

        calendar.setProperty("displayMode", window.property("monthMode"))
        assert _wait_for(lambda: not period_loader.property("active"))
        assert calendar.findChild(QQuickItem, "calendarPeriodGridLoader").property(
            "active"
        ) is False
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_multiple_selection_toggles_days(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        calendar = _calendar(window)
        calendar.setProperty("selectionMode", window.property("multipleMode"))
        _pump(40)

        for day in (4, 6, 9):
            _click(window, _day_cell(calendar, day))
        selected = list(_variant(calendar.property("selectedDates")))
        assert len(selected) == 3
        assert sorted(_day_of(item) for item in selected) == [4, 6, 9]
        assert _day_cell(calendar, 4).property("multiSelected") is True

        # Clicking a selected day removes it 再次点击已选日期会取消选择
        _click(window, _day_cell(calendar, 4))
        selected = list(_variant(calendar.property("selectedDates")))
        assert len(selected) == 2
        assert sorted(_day_of(item) for item in selected) == [6, 9]
        assert _day_cell(calendar, 4).property("multiSelected") is False

        _invoke(calendar, "clearSelection")
        assert list(_variant(calendar.property("selectedDates"))) == []
        # The single-selection day state is untouched by multi-selection
        # 多选不影响经典单选状态
        assert calendar.property("day") == 0
        assert calendar.property("selectionMode") == window.property("multipleMode")
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_blackout_dates_reject_clicks(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        calendar = _calendar(window)
        calendar.setProperty("blackoutDates", ["2026-03-15"])
        _pump(60)

        blocked = _day_cell(calendar, 15)
        assert blocked.property("isBlackout") is True
        assert _day_cell(calendar, 16).property("isBlackout") is False

        _click(window, blocked)
        assert calendar.property("day") == 0
        assert list(_variant(window.property("dayClicks"))) == []
        assert list(_variant(window.property("dateChanges"))) == []

        # A free neighbour day still commits 相邻可用日期仍可提交
        _click(window, _day_cell(calendar, 16))
        assert calendar.property("day") == 16
        assert list(_variant(window.property("dayClicks"))) == [16]
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_blackout_dates_also_block_multi_selection(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        calendar = _calendar(window)
        calendar.setProperty("selectionMode", window.property("multipleMode"))
        calendar.setProperty("blackoutDates", ["2026-03-15"])
        _pump(60)

        _click(window, _day_cell(calendar, 15))
        assert list(_variant(calendar.property("selectedDates"))) == []

        _click(window, _day_cell(calendar, 17))
        assert len(list(_variant(calendar.property("selectedDates")))) == 1
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_blackout_dates_block_adjacent_month_cells(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        calendar = _calendar(window)
        calendar.setProperty("blackoutDates", ["2026-04-01"])
        _pump(60)

        adjacent = [
            child
            for child in _descendants(calendar)
            if child.metaObject().indexOfProperty("displayDay") >= 0
            and child.property("isNextMonth") is True
            and child.property("displayDay") == 1
        ]
        assert len(adjacent) == 1
        assert adjacent[0].property("isBlackout") is True

        _click(window, adjacent[0])
        assert calendar.property("month") == 3
        assert calendar.property("day") == 0
        assert list(_variant(window.property("dayClicks"))) == []
        assert list(_variant(window.property("dateChanges"))) == []
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_range_mode_still_receives_its_gesture(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        calendar = _calendar(window)
        calendar.setProperty("rangeMode", True)
        _pump(40)
        _click(window, _day_cell(calendar, 10))

        clicks = list(_variant(window.property("rangeClicks")))
        assert len(clicks) == 1
        assert "2026" in clicks[0]
        assert list(_variant(window.property("dayClicks"))) == []
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_range_selection_enum_receives_range_gesture(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        calendar = _calendar(window)
        calendar.setProperty("selectionMode", window.property("rangeSelectionMode"))
        _pump(40)
        _click(window, _day_cell(calendar, 10))
        clicks = list(_variant(window.property("rangeClicks")))
        assert len(clicks) == 1
        assert "2026" in clicks[0]
        assert list(_variant(window.property("dayClicks"))) == []
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_today_button_is_opt_in_and_jumps_to_today(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        calendar = _calendar(window)
        today_loader = calendar.findChild(QQuickItem, "calendarTodayLoader")
        assert today_loader.property("active") is False

        calendar.setProperty("showTodayButton", True)
        assert _wait_for(lambda: today_loader.property("active"))
        button = today_loader.property("item")
        assert button is not None

        _click(window, button)
        assert calendar.property("year") == window.property("todayYear")
        assert calendar.property("month") == window.property("todayMonth")
        assert calendar.property("day") == window.property("todayDay")

        calendar.setProperty("showTodayButton", False)
        assert _wait_for(lambda: not today_loader.property("active"))
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
