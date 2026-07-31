# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Color picker dialog parent-chain regressions. 颜色选择对话框父链回归。"""

from pathlib import Path, PurePosixPath

import pytest
import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPoint,
    QPointF,
    QTimer,
    Qt,
    QUrl,
)
from PySide6.QtGui import QColor, QGuiApplication
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
    / "ColorPicker"
    / "_internal"
    / "ColorPickerDialog.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "color-picker-dialog-runtime.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property int redChannel: Enums.colorPickerMetrics.dialogRgbChannelR
    readonly property int greenChannel: Enums.colorPickerMetrics.dialogRgbChannelG
    readonly property int blueChannel: Enums.colorPickerMetrics.dialogRgbChannelB
    readonly property int dialogContentWidth: Enums.colorPickerMetrics.dialogContentWidth
    readonly property int dialogContentPadding: Enums.dialog.contentPadding
    readonly property int dialogActionsRowHeight: Enums.dialog.actionsRowHeight

    width: 900
    height: 800
    visible: true

    ColorPicker {
        objectName: "picker"
        type: Enums.colorPicker.type_dialog
        selectedColor: "#336699"
        defaultColor: "#112233"
        dialogTitle: "Pick"
        editColorText: "Custom"
        confirmText: "Apply"
        cancelText: "Back"
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
        _pump(20)
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
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isActive)
    picker = window.findChild(QQuickItem, "picker")
    assert picker is not None
    return engine, component, window, picker, warnings


def _dispose_scene(engine, component, window, picker) -> None:
    if picker.property("popupVisible"):
        assert QMetaObject.invokeMethod(picker, "close")
        _wait_for(lambda: not picker.property("popupVisible"))
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(20)


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = [root]
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.childItems())
    return result


def _dialog_card(dialog):
    matches = [
        item
        for item in _visual_descendants(dialog)
        if item.metaObject().className().startswith("QQuickRectangle")
        and item.clip()
    ]
    assert len(matches) == 1
    return matches[0]


def _dialog_content_column(dialog, expected_width):
    matches = [
        item
        for item in _visual_descendants(dialog)
        if item.metaObject().className().startswith("QQuickColumn")
        and item.width() == pytest.approx(expected_width)
    ]
    assert len(matches) == 1
    return matches[0]


def _trigger_button(picker):
    matches = [
        item
        for item in _visual_descendants(picker)
        if item.metaObject().className().startswith("ButtonCore")
        and item.metaObject().indexOfProperty("dropdownOpen") >= 0
    ]
    assert len(matches) == 1
    return matches[0]


def _open_dialog(picker, window):
    assert QMetaObject.invokeMethod(picker, "open")
    assert _wait_for(lambda: picker.property("popupVisible"))
    dialogs = [
        item
        for item in _visual_descendants(window.contentItem())
        if item.metaObject().className().startswith("ColorPickerDialog")
    ]
    assert len(dialogs) == 1
    dialog = dialogs[0]
    assert _wait_for(lambda: dialog.property("_isOpen"))
    card = _dialog_card(dialog)
    assert _wait_for(lambda: card.opacity() == pytest.approx(1.0))
    assert _wait_for(lambda: card.scale() == pytest.approx(1.0))
    return dialog, card


def _close_dialog(picker, dialog) -> None:
    assert QMetaObject.invokeMethod(picker, "close")
    assert _wait_for(lambda: not picker.property("popupVisible"))
    assert _wait_for(lambda: not dialog.property("_isClosing"))


def _hex_input(dialog):
    matches = [
        item
        for item in _visual_descendants(dialog)
        if item.metaObject().indexOfProperty("maximumLength") >= 0
        and item.property("maximumLength") == 6
        and item.metaObject().indexOfProperty("text") >= 0
    ]
    assert len(matches) == 1
    return matches[0]


def _rgb_inputs(dialog):
    inputs = [
        item
        for item in _visual_descendants(dialog)
        if item.metaObject().indexOfProperty("ch") >= 0
        and item.metaObject().indexOfProperty("text") >= 0
    ]
    assert len(inputs) == 3
    return {item.property("ch"): item for item in inputs}


def _panel(dialog):
    matches = [
        item
        for item in _visual_descendants(dialog)
        if item.metaObject().className().startswith("ColorPickerPanel")
    ]
    assert len(matches) == 1
    return matches[0]


def _brightness_area(dialog):
    matches = [
        item
        for item in _visual_descendants(dialog)
        if item.metaObject().className().startswith("QQuickMouseArea")
        and item.parentItem() is not None
        and item.parentItem().width() == pytest.approx(260)
        and item.parentItem().height() == pytest.approx(22)
    ]
    assert len(matches) == 1
    return matches[0]


def _brightness_handle(dialog):
    area = _brightness_area(dialog)
    matches = [
        item
        for item in area.parentItem().childItems()
        if item.metaObject().className().startswith("QQuickRectangle")
        and item.width() == pytest.approx(18)
        and item.height() == pytest.approx(18)
    ]
    assert len(matches) == 1
    return matches[0]


def _click_item(window: QQuickWindow, item: QQuickItem, x_ratio=0.5, y_ratio=0.5):
    point = item.mapToItem(
        window.contentItem(), QPointF(item.width() * x_ratio, item.height() * y_ratio)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )


def _rgb(color: QColor) -> tuple[int, int, int, int]:
    return color.getRgb()


def _new_visible_windows(windows_before, root_window):
    excluded = {
        shiboken6.getCppPointer(window)[0]
        for window in (*windows_before, root_window)
        if shiboken6.isValid(window)
    }
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and shiboken6.getCppPointer(window)[0] not in excluded
    ]


def test_color_picker_dialog_hover_prewarms_hidden_content(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, picker, warnings = _create_scene()
    try:
        QTest.mouseMove(
            window, QPoint(round(window.width() - 12), round(window.height() - 12))
        )
        _pump()
        picker.setProperty("_dialogRequested", False)
        _pump()
        assert not picker.property("_dialogRequested")
        assert not any(
            item.metaObject().className().startswith("ColorPickerDialog")
            for item in _visual_descendants(picker)
        )
        trigger = _trigger_button(picker)
        point = trigger.mapToItem(
            window.contentItem(), QPointF(trigger.width() / 2, trigger.height() / 2)
        )
        QTest.mouseMove(window, point.toPoint())

        assert _wait_for(lambda: picker.property("_dialogRequested"))
        assert any(
            item.metaObject().className().startswith("ColorPickerDialog")
            for item in _visual_descendants(picker)
        )
        assert not picker.property("popupVisible")
        assert _new_visible_windows(windows_before, window) == []
        assert warnings == []
    finally:
        QTest.mouseMove(
            window, QPoint(round(window.width() - 12), round(window.height() - 12))
        )
        _pump()
        _dispose_scene(engine, component, window, picker)


def test_color_picker_dialog_preserves_public_parent_geometry(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, picker, warnings = _create_scene()
    try:
        dialog, card = _open_dialog(picker, window)
        panel = _panel(dialog)
        rgb_inputs = _rgb_inputs(dialog)
        content_column = _dialog_content_column(
            dialog, window.property("dialogContentWidth")
        )
        previews = [
            item
            for item in _visual_descendants(dialog)
            if item.metaObject().className().startswith("QQuickRectangle")
            and item.width() == pytest.approx(46)
            and item.height() == pytest.approx(126)
        ]

        assert card.width() == pytest.approx(
            content_column.width() + window.property("dialogContentPadding")
        )
        assert card.height() == pytest.approx(
            content_column.property("implicitHeight")
            + window.property("dialogActionsRowHeight")
            + window.property("dialogContentPadding")
        )
        assert (panel.width(), panel.height()) == pytest.approx((260, 260))
        assert len(previews) == 2
        assert _rgb(dialog.property("selectedColor")) == (51, 102, 153, 255)
        assert _rgb(dialog.property("initialColor")) == (51, 102, 153, 255)
        assert dialog.property("_hue") == pytest.approx(7 / 12)
        assert dialog.property("_saturation") == pytest.approx(2 / 3)
        assert dialog.property("_brightness") == pytest.approx(0.6)
        assert dialog.property("_alpha") == 255
        assert _hex_input(dialog).property("text") == "336699"
        assert set(rgb_inputs) == {
            window.property("redChannel"),
            window.property("greenChannel"),
            window.property("blueChannel"),
        }
        assert {
            channel: item.property("text") for channel, item in rgb_inputs.items()
        } == {
            window.property("redChannel"): "51",
            window.property("greenChannel"): "102",
            window.property("blueChannel"): "153",
        }
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
        _close_dialog(picker, dialog)
    finally:
        _dispose_scene(engine, component, window, picker)


def test_color_picker_dialog_maps_panel_and_brightness_clicks(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, picker, warnings = _create_scene()
    try:
        dialog, _card = _open_dialog(picker, window)
        updated = []
        parent_changed = []
        dialog.colorUpdated.connect(updated.append)
        picker.colorChanged.connect(parent_changed.append)

        _click_item(window, _panel(dialog), x_ratio=0.25, y_ratio=0.75)
        _pump(20)
        expected = QColor.fromHsvF(0.25, 0.25, 0.6, 1.0)
        assert _rgb(dialog.property("selectedColor")) == _rgb(expected)
        assert _rgb(picker.property("selectedColor")) == (51, 102, 153, 255)
        assert len(updated) == 1
        assert len(parent_changed) == 1
        assert _rgb(parent_changed[0]) == _rgb(expected)

        _click_item(window, _brightness_area(dialog), x_ratio=0.5)
        _pump(20)
        expected = QColor.fromHsvF(0.25, 0.25, 0.5, 1.0)
        assert _rgb(dialog.property("selectedColor")) == _rgb(expected)
        assert _rgb(picker.property("selectedColor")) == (51, 102, 153, 255)
        assert len(updated) == 2
        assert len(parent_changed) == 2
        assert _rgb(parent_changed[1]) == _rgb(expected)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window, picker)


def test_color_picker_dialog_brightness_handle_tracks_drag_immediately(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, picker, warnings = _create_scene()
    try:
        dialog, _card = _open_dialog(picker, window)
        area = _brightness_area(dialog)
        handle = _brightness_handle(dialog)
        press_point = area.mapToItem(
            window.contentItem(), QPointF(area.width() * 0.6, area.height() / 2)
        ).toPoint()
        drag_point = area.mapToItem(
            window.contentItem(), QPointF(area.width() * 0.85, area.height() / 2)
        ).toPoint()

        QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=press_point)
        QTest.mouseMove(window, drag_point, delay=1)

        assert dialog.property("_brightness") == pytest.approx(0.85, abs=0.01)
        expected_x = dialog.property("_brightness") * (
            handle.parentItem().width() - handle.width()
        )
        assert handle.x() == pytest.approx(expected_x, abs=1)

        QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=drag_point)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window, picker)


def test_color_picker_dialog_accepts_rejects_and_closes_parent(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, picker, warnings = _create_scene()
    try:
        accepted = []
        selected = []
        rejected = []
        picker.accepted.connect(accepted.append)
        picker.colorSelected.connect(selected.append)
        picker.rejected.connect(lambda: rejected.append(True))

        dialog, _card = _open_dialog(picker, window)
        yes_button = window.findChild(QQuickItem, "yesButton")
        assert yes_button is not None
        _click_item(window, yes_button)
        assert _wait_for(lambda: not picker.property("popupVisible"))
        assert _wait_for(lambda: not dialog.property("_isClosing"))
        assert len(accepted) == 1
        assert len(selected) == 1
        assert _rgb(accepted[0]) == (51, 102, 153, 255)

        picker.setProperty("selectedColor", QColor("#445566"))
        dialog, _card = _open_dialog(picker, window)
        cancel_button = window.findChild(QQuickItem, "cancelButton")
        assert cancel_button is not None
        _click_item(window, cancel_button)
        assert _wait_for(lambda: not picker.property("popupVisible"))
        assert _wait_for(lambda: not dialog.property("_isClosing"))
        assert rejected == [True]
        assert _rgb(picker.property("selectedColor")) == (68, 85, 102, 255)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window, picker)


def test_color_picker_dialog_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        item for item in violations if item.rule in {"QML008", "QML009"}
    ] == []


def test_color_picker_dialog_uses_range_and_spacing_tokens():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    for token in (
        "Enums.colorPickerMetrics.dialogCustomRowSpacing",
        "Enums.colorPickerMetrics.channelMinValue",
        "Enums.opacityLevel.invisible",
        "Enums.opacityLevel.visible",
    ):
        assert token in source
    for literal in (
        "Math.max(0, Math.min(1",
        "GradientStop { position: 0",
        "validator: IntValidator { bottom: 0",
        "Enums.spacing.xxxl * 2 + Enums.spacing.l",
    ):
        assert literal not in source
