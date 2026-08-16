# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Input leaf convention regressions. 输入叶组件规范回归。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import QEventLoop, QMetaObject, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
CALENDAR_NAV_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "DatePicker"
    / "_internal"
    / "CalendarNavButton.qml"
)
DATE_TIME_BUTTONS_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "Picker"
    / "_internal"
    / "DateTimeButtons.qml"
)
DATE_TIME_PICKER_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "Picker"
    / "DateTimePicker.qml"
)
DATE_TIME_PICKER_INIT_TIMER_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "Picker"
    / "_internal"
    / "DateTimePickerInitTimer.qml"
)
DATE_TIME_PICKER_POPUP_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "Picker"
    / "_internal"
    / "DateTimePickerPopup.qml"
)
DATE_TIME_PICKER_DISPLAY_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "Picker"
    / "_internal"
    / "DateTimePickerDisplay.qml"
)
FOCUS_LINE_SOURCE = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "inputs" / "FocusLine.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "input-leaf-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property string expectedUpIcon: Enums.icon.chevron_up
    readonly property string expectedDownIcon: Enums.icon.chevron_down
    readonly property color expectedTransparent: Enums.transparent
    readonly property real expectedRadius: Enums.radius.small
    readonly property int expectedPrimaryStyle: Enums.button.style_primary
    readonly property int expectedDefaultStyle: Enums.button.style_default
    readonly property real expectedSpacingL: Enums.spacing.l
    readonly property real expectedSpacingXl: Enums.spacing.xl
    readonly property color expectedAccent: Enums.accentColor
    readonly property real expectedBorderNormal: Enums.border.normal
    readonly property real expectedFocusLineHeight: Enums.controlSize.focusLineHeight

    width: 256
    height: 300

    CalendarPickerCore {
        id: calendar
        objectName: "calendar"
        anchors.fill: parent
        year: 2026
        month: 7
    }

    DateTimePicker {
        id: dateTimePicker
        objectName: "dateTimePicker"
        width: 280
        type: Enums.picker.type_datetime
        timePrecision: Enums.picker.time_second
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
    _pump(20)
    assert warnings == []
    return engine, component, root, warnings


def _new_visible_windows(windows_before):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
    ]


def _descendants(root):
    return root.findChildren(QObject)


def _nav_buttons(calendar):
    matches = []
    for child in _descendants(calendar):
        if child.metaObject().indexOfProperty("icon") < 0:
            continue
        if (child.property("width"), child.property("height")) != (32.0, 34.0):
            continue
        mouse_areas = [
            item
            for item in child.children()
            if item.metaObject().indexOfProperty("containsMouse") >= 0
            and item.metaObject().indexOfProperty("hoverEnabled") >= 0
        ]
        if len(mouse_areas) == 1:
            matches.append((child, mouse_areas[0]))
    assert len(matches) == 2, [item.metaObject().className() for item, _ in matches]
    return sorted(matches, key=lambda pair: pair[0].property("x"))


def _date_time_parts(picker):
    areas = [
        child
        for child in _descendants(picker)
        if child.metaObject().indexOfProperty("control") >= 0
        and child.property("control") == picker
        and child.metaObject().indexOfProperty("height") >= 0
        and child.property("height") == 52.0
    ]
    assert len(areas) == 1, [item.metaObject().className() for item in areas]
    rows = [
        child
        for child in areas[0].children()
        if child.metaObject().className() == "QQuickRow"
    ]
    assert len(rows) == 1, [item.metaObject().className() for item in rows]
    buttons = [
        child
        for child in rows[0].children()
        if child.metaObject().indexOfProperty("style") >= 0
        and child.metaObject().indexOfProperty("text") >= 0
    ]
    assert len(buttons) == 2, [item.metaObject().className() for item in buttons]
    return areas[0], rows[0], buttons


def _date_time_popups(picker):
    return [
        child
        for child in _descendants(picker)
        if child.metaObject().indexOfProperty("popupWidth") >= 0
        and child.metaObject().indexOfProperty("isOpen") >= 0
    ]


def _date_time_popup(picker):
    matches = _date_time_popups(picker)
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _date_time_popup_content(picker):
    alias_names = (
        "col2Loader", "col3Loader", "hourWheelLoader",
        "minuteWheelLoader", "secondWheelLoader", "ampmWheelLoader",
    )
    matches = [
        child
        for child in _descendants(picker)
        if all(child.metaObject().indexOfProperty(name) >= 0 for name in alias_names)
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0], alias_names


def _picker_wheel_area(popup_content):
    matches = [
        child
        for child in _descendants(popup_content)
        if child.metaObject().indexOfProperty("_wheelWidth") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _picker_loaders(wheel_area):
    rows = [
        child
        for child in wheel_area.childItems()
        if child.metaObject().className().startswith("QQuickRow")
    ]
    assert len(rows) == 1, [item.metaObject().className() for item in rows]
    loaders = [
        child
        for child in rows[0].childItems()
        if child.metaObject().className().startswith("QQuickLoader")
    ]
    assert len(loaders) == 7, [item.metaObject().className() for item in loaders]
    return loaders


def _assert_loader_alias_metadata(popup_content, alias_names):
    meta_object = popup_content.metaObject()
    for name in alias_names:
        meta_property = meta_object.property(meta_object.indexOfProperty(name))
        assert meta_property.isAlias()
        assert meta_property.isReadable()
        assert not meta_property.isWritable()
        assert meta_property.typeName() == "QQuickLoader*"


def _assert_picker_popup_runtime(picker):
    popup_content, alias_names = _date_time_popup_content(picker)
    assert popup_content.property("control") == picker
    _assert_loader_alias_metadata(popup_content, alias_names)
    wheel_area = _picker_wheel_area(popup_content)
    loaders = _picker_loaders(wheel_area)
    assert [loader.property("active") for loader in loaders] == [
        True, True, True, True, True, True, False,
    ]
    assert wheel_area.property("_wheelWidth") == (
        wheel_area.property("width") / picker.property("_totalColCount")
    )
    expected_width = wheel_area.property("_wheelWidth")
    assert [loader.property("width") for loader in loaders] == [
        expected_width, expected_width, expected_width,
        expected_width, expected_width, expected_width, 0.0,
    ]
    picker.setProperty("width", 360.0)
    _pump()
    resized_width = wheel_area.property("_wheelWidth")
    assert resized_width != expected_width
    assert resized_width == (
        wheel_area.property("width") / picker.property("_totalColCount")
    )
    assert [loader.property("width") for loader in loaders] == [
        resized_width, resized_width, resized_width,
        resized_width, resized_width, resized_width, 0.0,
    ]


def _assert_date_time_runtime(root, picker):
    area, row, buttons = _date_time_parts(picker)
    popup = _date_time_popup(picker)
    button_text_by_style = {
        item.property("style"): item.property("text") for item in buttons
    }
    expected_width = (
        area.property("width")
        - root.property("expectedSpacingL")
        - root.property("expectedSpacingXl")
    ) / 2
    assert area.property("control") == picker
    assert area.property("height") == 52.0
    assert row.property("spacing") == root.property("expectedSpacingL")
    assert button_text_by_style == {
        root.property("expectedPrimaryStyle"): picker.property("_confirmText"),
        root.property("expectedDefaultStyle"): picker.property("_cancelText"),
    }
    assert all(item.property("width") == expected_width for item in buttons)
    assert not picker.property("isOpen")
    assert not popup.property("isOpen")
    assert popup.property("_prewarmed")


def _focus_line(picker):
    matches = [
        child
        for child in _descendants(picker)
        if child.metaObject().indexOfProperty("showLine") >= 0
        and child.metaObject().indexOfProperty("lineColor") >= 0
        and child.metaObject().indexOfProperty("parentRadius") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    child_items = matches[0].childItems()
    rectangles = [
        child
        for child in child_items
        if child.metaObject().className().startswith("QQuickRectangle")
    ]
    assert len(rectangles) == 1, [
        item.metaObject().className() for item in child_items
    ]
    return matches[0], rectangles[0]


def _assert_focus_line_runtime(root, picker):
    focus_line, rectangle = _focus_line(picker)
    assert not focus_line.property("showLine")
    assert focus_line.property("lineColor") == root.property("expectedAccent")
    assert focus_line.property("parentRadius") == picker.property("radius")
    assert focus_line.property("height") == root.property("expectedBorderNormal")
    assert focus_line.property("clip")
    assert rectangle.property("width") == 0.0
    assert rectangle.property("height") == root.property("expectedFocusLineHeight")
    assert rectangle.property("radius") == focus_line.property("parentRadius")
    assert rectangle.property("color") == focus_line.property("lineColor")


def test_calendar_nav_button_parent_chain(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene()
    try:
        calendar = root.findChild(QObject, "calendar")
        assert calendar is not None
        nav_buttons = _nav_buttons(calendar)
        assert [item.property("icon") for item, _ in nav_buttons] == [
            root.property("expectedUpIcon"),
            root.property("expectedDownIcon"),
        ]
        for item, mouse_area in nav_buttons:
            assert item.property("color") == root.property("expectedTransparent")
            assert item.property("radius") == root.property("expectedRadius")
            assert mouse_area.property("hoverEnabled")
            assert not mouse_area.property("containsMouse")
            assert not mouse_area.property("pressed")
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_date_time_buttons_parent_chain(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene()
    try:
        picker = root.findChild(QObject, "dateTimePicker")
        assert picker is not None
        assert QMetaObject.invokeMethod(picker, "_prewarmPopupContent")
        _pump()
        _assert_date_time_runtime(root, picker)
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_focus_line_parent_chain(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene()
    try:
        picker = root.findChild(QObject, "dateTimePicker")
        assert picker is not None
        assert not picker.property("isOpen")
        _assert_focus_line_runtime(root, picker)
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_date_time_picker_popup_parent_chain(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene()
    try:
        picker = root.findChild(QObject, "dateTimePicker")
        assert picker is not None
        assert not picker.property("isOpen")
        assert _date_time_popups(picker) == []
        assert not picker.property("_popupContentRequested")

        assert QMetaObject.invokeMethod(picker, "_prewarmPopupContent")
        assert _wait_for(lambda: picker.property("_popupContentRequested"))
        assert _wait_for(lambda: len(_date_time_popups(picker)) == 1)
        popup = _date_time_popup(picker)
        assert _wait_for(lambda: popup.property("_prewarmed"))
        _assert_picker_popup_runtime(picker)
        assert not picker.property("isOpen")
        assert not popup.property("isOpen")
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_calendar_nav_button_source_conventions():
    source = CALENDAR_NAV_SOURCE.read_text(encoding="utf-8")
    path = PurePosixPath(CALENDAR_NAV_SOURCE.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []


def test_date_time_buttons_source_conventions():
    source = DATE_TIME_BUTTONS_SOURCE.read_text(encoding="utf-8")
    path = PurePosixPath(DATE_TIME_BUTTONS_SOURCE.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []


def test_date_time_picker_source_uses_standard_sections():
    source = DATE_TIME_PICKER_SOURCE.read_text(encoding="utf-8")
    path = PurePosixPath(DATE_TIME_PICKER_SOURCE.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []


def test_date_time_picker_init_timer_source_uses_standard_sections():
    source = DATE_TIME_PICKER_INIT_TIMER_SOURCE.read_text(encoding="utf-8")
    path = PurePosixPath(
        DATE_TIME_PICKER_INIT_TIMER_SOURCE.relative_to(ROOT).as_posix()
    )
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []


def test_date_time_picker_popup_source_uses_standard_sections():
    source = DATE_TIME_PICKER_POPUP_SOURCE.read_text(encoding="utf-8")
    path = PurePosixPath(DATE_TIME_PICKER_POPUP_SOURCE.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    for name in (
        "col2Loader", "col3Loader", "hourWheelLoader",
        "minuteWheelLoader", "secondWheelLoader", "ampmWheelLoader",
    ):
        assert source.count(f"property alias {name}: {name}") == 1
        assert source.count(f"id: {name}") == 1
    assert [
        item
        for item in violations
        if item.rule in {"QML008", "QML009"}
    ] == []


def test_date_time_picker_display_source_uses_standard_sections():
    source = DATE_TIME_PICKER_DISPLAY_SOURCE.read_text(encoding="utf-8")
    path = PurePosixPath(DATE_TIME_PICKER_DISPLAY_SOURCE.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        item
        for item in violations
        if item.rule in {"QML008", "QML009"}
    ] == []


def test_focus_line_source_conventions():
    source = FOCUS_LINE_SOURCE.read_text(encoding="utf-8")
    path = PurePosixPath(FOCUS_LINE_SOURCE.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
