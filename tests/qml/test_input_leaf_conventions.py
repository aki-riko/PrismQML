# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Input leaf convention regressions. 输入叶组件规范回归。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
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

    width: 256
    height: 300

    CalendarPickerCore {
        id: calendar
        objectName: "calendar"
        anchors.fill: parent
        year: 2026
        month: 7
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
    result = []
    pending = list(root.children())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.children())
    return result


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


def test_calendar_nav_button_source_conventions():
    source = CALENDAR_NAV_SOURCE.read_text(encoding="utf-8")
    path = PurePosixPath(CALENDAR_NAV_SOURCE.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
