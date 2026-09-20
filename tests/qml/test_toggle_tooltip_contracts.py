# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Toggle tooltip API and lifecycle contracts. Toggle 工具提示 API 与生命周期合同。"""

from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
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


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "toggle-tooltip-contracts.qml")
)
TOOLTIP_PROPERTY_NAMES = (
    "toolTipText",
    "toolTipShowDelay",
    "toolTipHideDelay",
    "toolTipDuration",
    "toolTipPosition",
    "toolTipTextAlignment",
)
TIMER_SETTLE_MS = 100
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import PrismQML

Window {
    id: root

    readonly property int testShowDelay: Enums.duration.none
    readonly property int testReentryHideDelay: Enums.duration.normal
    readonly property int testDuration: Enums.duration.persistent
    readonly property int positionTop: Enums.position.top
    readonly property int positionRight: Enums.position.right
    readonly property int positionBottom: Enums.position.bottom
    readonly property int positionLeft: Enums.position.left
    readonly property int alignLeft: Text.AlignLeft
    readonly property int alignCenter: Text.AlignHCenter
    readonly property int alignRight: Text.AlignRight
    readonly property int alignJustify: Text.AlignJustify

    width: 720
    height: 320
    visible: true

    Toggle {
        objectName: "toggle"
        x: 40
        y: 60
        text: "Toggle"
        toolTipText: "Toggle tooltip"
        toolTipShowDelay: root.testShowDelay
        toolTipHideDelay: root.testReentryHideDelay
        toolTipDuration: root.testDuration
        toolTipPosition: root.positionTop
        toolTipTextAlignment: root.alignLeft
    }

    CheckBox {
        objectName: "checkBox"
        x: 210
        y: 60
        text: "CheckBox"
        toolTipText: "CheckBox tooltip"
        toolTipShowDelay: root.testShowDelay
        toolTipHideDelay: root.testReentryHideDelay
        toolTipDuration: root.testDuration
        toolTipPosition: root.positionRight
        toolTipTextAlignment: root.alignCenter
    }

    RadioButton {
        objectName: "radioButton"
        x: 40
        y: 190
        text: "RadioButton"
        toolTipText: "RadioButton tooltip"
        toolTipShowDelay: root.testShowDelay
        toolTipHideDelay: root.testReentryHideDelay
        toolTipDuration: root.testDuration
        toolTipPosition: root.positionBottom
        toolTipTextAlignment: root.alignRight
    }

    ToggleSwitch {
        objectName: "toggleSwitch"
        x: 210
        y: 190
        text: "ToggleSwitch"
        toolTipText: "ToggleSwitch tooltip"
        toolTipShowDelay: root.testShowDelay
        toolTipHideDelay: root.testReentryHideDelay
        toolTipDuration: root.testDuration
        toolTipPosition: root.positionLeft
        toolTipTextAlignment: root.alignJustify
    }

    RowLayout {
        id: compactLayout
        objectName: "compactLayout"
        x: 40
        y: 260
        width: 440

        Toggle {
            objectName: "layoutToggle"
            text: "Layout Toggle"
        }

        Item {
            Layout.fillWidth: true
        }
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


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


def _load_scene_component(engine):
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    return component


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = _load_scene_component(engine)
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isExposed)
    controls = {
        name: window.findChild(QQuickItem, name)
        for name in ("toggle", "checkBox", "radioButton", "toggleSwitch")
    }
    assert all(controls.values())
    assert _wait_for(
        lambda: all(
            control.findChild(QObject, "_hoverArea") is not None
            for control in controls.values()
        )
    )
    return engine, component, window, controls, warnings


def _dispose_scene(qapp, engine, component, window) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def _assert_tooltip_properties(control, text, position, alignment, window):
    assert all(
        control.metaObject().indexOfProperty(property_name) >= 0
        for property_name in TOOLTIP_PROPERTY_NAMES
    )
    assert control.property("toolTipText") == text
    assert control.property("toolTipShowDelay") == window.property("testShowDelay")
    assert control.property("toolTipHideDelay") == window.property(
        "testReentryHideDelay"
    )
    assert control.property("toolTipDuration") == window.property("testDuration")
    assert control.property("toolTipPosition") == position
    assert control.property("toolTipTextAlignment") == alignment
    assert control.width() == control.implicitWidth()
    assert control.height() == control.implicitHeight()
    assert QMetaObject.invokeMethod(control, "hideToolTip")


def _expected_tooltips(window):
    return {
        "toggle": (
            "Toggle tooltip",
            window.property("positionTop"),
            window.property("alignLeft"),
        ),
        "checkBox": (
            "CheckBox tooltip",
            window.property("positionRight"),
            window.property("alignCenter"),
        ),
        "radioButton": (
            "RadioButton tooltip",
            window.property("positionBottom"),
            window.property("alignRight"),
        ),
        "toggleSwitch": (
            "ToggleSwitch tooltip",
            window.property("positionLeft"),
            window.property("alignJustify"),
        ),
    }


def _move_outside(window):
    QTest.mouseMove(window, QPoint(window.width() - 5, window.height() - 5))


def _show_tooltip(window, control):
    _move_outside(window)
    QTest.mouseMove(window, _point_for(window, control))
    assert _wait_for(lambda: control.findChild(QObject, "_toolTip") is not None)
    tooltip = control.findChild(QObject, "_toolTip")
    assert tooltip is not None
    assert _wait_for(lambda: tooltip.property("visible") is True)
    return tooltip


def _switch_indicator(control):
    matches = [
        item
        for item in control.findChildren(QQuickItem)
        if item.metaObject().indexOfProperty("_trackColor") >= 0
        and item.metaObject().indexOfProperty("checkedColor") >= 0
    ]
    assert len(matches) == 1
    return matches[0]


def test_toggle_variants_expose_widget_tooltip_api(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    try:
        expected = _expected_tooltips(window)
        for name, control in controls.items():
            _assert_tooltip_properties(control, *expected[name], window)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(qapp, engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_toggle_keeps_compact_geometry_inside_row_layout(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, _, warnings = _create_scene()
    try:
        layout = window.findChild(QQuickItem, "compactLayout")
        layout_toggle = window.findChild(QQuickItem, "layoutToggle")
        assert layout is not None
        assert layout_toggle is not None
        assert layout_toggle.width() == layout_toggle.implicitWidth()
        assert layout_toggle.height() == layout_toggle.implicitHeight()
        assert layout_toggle.width() < layout.width()
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(qapp, engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_checkbox_tooltip_real_hover_show_and_hide_lifecycle(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    try:
        check_box = controls["checkBox"]

        tooltip = _show_tooltip(window, check_box)
        assert _wait_for(
            lambda: len(_new_visible_windows(windows_before, window)) == 1
        )
        popup_window = _new_visible_windows(windows_before, window)[0]
        assert isinstance(popup_window, QQuickWindow)

        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            _point_for(window, check_box),
        )
        assert _wait_for(lambda: check_box.property("checked") is True)

        _move_outside(window)
        assert _wait_for(lambda: tooltip.property("visible") is False)
        assert _wait_for(
            lambda: _new_visible_windows(windows_before, window) == []
        )
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_checkbox_reentry_cancels_pending_tooltip_hide(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    try:
        check_box = controls["checkBox"]
        tooltip = _show_tooltip(window, check_box)
        _move_outside(window)
        _pump(TIMER_SETTLE_MS)
        QTest.mouseMove(window, _point_for(window, check_box))
        _pump(check_box.property("toolTipHideDelay") + TIMER_SETTLE_MS)
        assert tooltip.property("visible") is True
        _move_outside(window)
        assert _wait_for(lambda: tooltip.property("visible") is False)
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_toggle_switch_text_to_track_keeps_tooltip_visible(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    try:
        toggle_switch = controls["toggleSwitch"]
        text_point = toggle_switch.mapToItem(
            window.contentItem(),
            QPointF(toggle_switch.width() - 1, toggle_switch.height() / 2),
        )
        _move_outside(window)
        QTest.mouseMove(window, QPoint(round(text_point.x()), round(text_point.y())))
        tooltip = _show_tooltip(window, toggle_switch)
        QTest.mouseMove(window, QPoint(round(text_point.x()), round(text_point.y())))
        _pump(TIMER_SETTLE_MS)
        QTest.mouseMove(window, _point_for(window, _switch_indicator(toggle_switch)))
        _pump(toggle_switch.property("toolTipHideDelay") + TIMER_SETTLE_MS)
        assert tooltip.property("visible") is True
        _move_outside(window)
        assert _wait_for(lambda: tooltip.property("visible") is False)
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)
        assert _new_visible_windows(windows_before) == []
