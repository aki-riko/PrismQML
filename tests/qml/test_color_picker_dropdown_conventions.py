# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Color picker dropdown parent-chain regressions. 颜色选择下拉框父链回归。"""

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
    / "ColorPickerDropdown.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "color-picker-dropdown-runtime.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property int dropdownFeature: Enums.button.feature_dropdown
    readonly property var checkIcon: Enums.icon.checkmark
    readonly property var dismissIcon: Enums.icon.dismiss
    readonly property int rgbMode: Enums.colorPicker.mode_rgb
    readonly property int hsvMode: Enums.colorPicker.mode_hsv
    readonly property int redChannel: Enums.colorPickerMetrics.dialogRgbChannelR
    readonly property int greenChannel: Enums.colorPickerMetrics.dialogRgbChannelG
    readonly property int blueChannel: Enums.colorPickerMetrics.dialogRgbChannelB
    readonly property int alphaChannel: Enums.colorPickerMetrics.channelAlphaIndex

    width: 500
    height: 400
    visible: true

    ColorPicker {
        objectName: "picker"
        x: 80
        y: 60
        selectedColor: "#336699"
        defaultColor: "#112233"
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


def _new_visible_windows(windows_before, *allowed):
    excluded = {
        shiboken6.getCppPointer(window)[0]
        for window in (*windows_before, *allowed)
        if shiboken6.isValid(window)
    }
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and shiboken6.getCppPointer(window)[0] not in excluded
    ]


def _popup_core(picker):
    matches = [
        item
        for item in _visual_descendants(picker)
        if item.metaObject().className().startswith("PopupWindowCore")
        and item.metaObject().indexOfProperty("popupWidth") >= 0
        and item.metaObject().indexOfProperty("isClosing") >= 0
        and item.parentItem() is picker
    ]
    assert len(matches) == 1
    return matches[0]


def _open_dropdown(picker, root_window, windows_before):
    popup_core = _popup_core(picker)
    assert QMetaObject.invokeMethod(picker, "open")
    assert _wait_for(lambda: picker.property("popupVisible"))
    excluded = {
        shiboken6.getCppPointer(window)[0]
        for window in (*windows_before, root_window)
        if shiboken6.isValid(window)
    }

    def visible_popup_windows():
        return [
            window
            for window in QGuiApplication.topLevelWindows()
            if isinstance(window, QQuickWindow)
            and window.isVisible()
            and shiboken6.getCppPointer(window)[0] not in excluded
        ]

    assert _wait_for(lambda: len(visible_popup_windows()) == 1)
    popup_window = visible_popup_windows()[0]
    dropdowns = [
        item
        for item in _visual_descendants(popup_window.contentItem())
        if item.metaObject().className().startswith("ColorPickerDropdown")
    ]
    assert len(dropdowns) == 1
    dropdown = dropdowns[0]
    popup_window.requestActivate()
    assert _wait_for(popup_window.isActive)
    assert _wait_for(lambda: dropdown.property("implicitHeight") == pytest.approx(487))
    assert _wait_for(lambda: popup_core.property("isOpen"))
    assert _wait_for(
        lambda: popup_core.property("_clipHeight")
        == pytest.approx(popup_core.property("popupHeight"))
    )
    assert _wait_for(lambda: popup_core.property("_offsetY") == pytest.approx(0.0))
    return popup_core, popup_window, dropdown


def _close_dropdown(picker, popup_core, popup_window) -> None:
    assert QMetaObject.invokeMethod(picker, "close")
    assert _wait_for(lambda: not picker.property("popupVisible"))
    assert _wait_for(lambda: not popup_core.property("isClosing"))
    assert _wait_for(lambda: not popup_window.isVisible())


def _channel_sliders(dropdown):
    sliders = [
        item
        for item in _visual_descendants(dropdown)
        if item.metaObject().className().startswith("ColorPickerChannelSlider")
    ]
    assert len(sliders) == 4
    return {slider.property("channel"): slider for slider in sliders}


def _hex_input(dropdown):
    matches = [
        item
        for item in _visual_descendants(dropdown)
        if item.metaObject().indexOfProperty("text") >= 0
        and item.metaObject().indexOfProperty("selectByMouse") >= 0
        and str(item.property("text")).startswith("#")
    ]
    assert len(matches) == 1
    return matches[0]


def _mode_area(dropdown):
    matches = [
        item
        for item in _visual_descendants(dropdown)
        if item.metaObject().className().startswith("QQuickMouseArea")
        and item.property("hoverEnabled") is True
        and item.parentItem().width() == pytest.approx(80)
    ]
    assert len(matches) == 1
    return matches[0]


def _action_button(dropdown, icon):
    matches = [
        item
        for item in _visual_descendants(dropdown)
        if item.metaObject().className().startswith("ButtonCore")
        and item.metaObject().indexOfProperty("icon") >= 0
        and item.property("icon") == icon
    ]
    assert len(matches) == 1
    return matches[0]


def test_color_picker_dropdown_hover_prewarms_hidden_content(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, picker, warnings = _create_scene()
    try:
        popup_core = _popup_core(picker)
        assert not picker.property("_popupContentRequested")
        assert not any(
            item.metaObject().className().startswith("ColorPickerDropdown")
            for item in picker.findChildren(QQuickItem)
        )
        trigger = _trigger_button(picker, window.property("dropdownFeature"))
        QTest.mouseMove(
            window, QPoint(round(window.width() - 12), round(window.height() - 12))
        )
        _pump()
        point = trigger.mapToItem(
            window.contentItem(), QPointF(trigger.width() / 2, trigger.height() / 2)
        )
        QTest.mouseMove(window, point.toPoint())

        assert _wait_for(lambda: picker.property("_popupContentRequested"))
        assert _wait_for(lambda: popup_core.property("_prewarmed"))
        assert any(
            item.metaObject().className().startswith("ColorPickerDropdown")
            for item in picker.findChildren(QQuickItem)
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


def _trigger_button(picker, feature):
    matches = [
        item
        for item in _visual_descendants(picker)
        if item.metaObject().className().startswith("ButtonCore")
        and item.property("feature") == feature
    ]
    assert len(matches) == 1
    return matches[0]


def _click_item(window: QQuickWindow, item: QQuickItem) -> None:
    point = item.mapToItem(
        window.contentItem(), QPointF(item.width() / 2, item.height() / 2)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )


def _rgb(color: QColor) -> tuple[int, int, int, int]:
    return color.getRgb()


def test_color_picker_dropdown_preserves_public_parent_geometry(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, picker, warnings = _create_scene()
    try:
        popup_core, popup_window, dropdown = _open_dropdown(
            picker, window, windows_before
        )
        descendants = _visual_descendants(dropdown)
        panels = [
            item for item in descendants
            if item.metaObject().className().startswith("ColorPickerPanel")
        ]
        brightness_sliders = [
            item for item in descendants
            if item.metaObject().className().startswith("ColorPickerBrightnessSlider")
        ]
        sliders = _channel_sliders(dropdown)

        assert (popup_window.width(), popup_window.height()) == (336, 496)
        assert (dropdown.width(), dropdown.height()) == pytest.approx((312, 472))
        assert dropdown.property("implicitWidth") == pytest.approx(300)
        assert dropdown.property("implicitHeight") == pytest.approx(487)
        assert dropdown.property("_hue") == pytest.approx(7 / 12)
        assert dropdown.property("_saturation") == pytest.approx(2 / 3)
        assert dropdown.property("_brightness") == pytest.approx(0.6)
        assert dropdown.property("_alpha") == 255
        assert len(panels) == 1
        assert (panels[0].width(), panels[0].height()) == pytest.approx((288, 220))
        assert len(brightness_sliders) == 1
        assert (
            brightness_sliders[0].width(),
            brightness_sliders[0].height(),
        ) == pytest.approx((288, 20))
        assert set(sliders) == {
            window.property("redChannel"),
            window.property("greenChannel"),
            window.property("blueChannel"),
            window.property("alphaChannel"),
        }
        assert all(slider.width() == pytest.approx(288) for slider in sliders.values())
        assert all(slider.height() == pytest.approx(24) for slider in sliders.values())
        assert _hex_input(dropdown).property("text") == "#ff336699"
        assert warnings == []
        assert _new_visible_windows(windows_before, window, popup_window) == []

        _close_dropdown(picker, popup_core, popup_window)
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window, picker)


def test_color_picker_dropdown_maps_mode_and_channel_updates(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, picker, warnings = _create_scene()
    try:
        _popup_core_item, popup_window, dropdown = _open_dropdown(
            picker, window, windows_before
        )
        assert dropdown.property("colorMode") == window.property("rgbMode")
        _click_item(popup_window, _mode_area(dropdown))
        _pump(20)
        assert dropdown.property("colorMode") == window.property("hsvMode")

        changed = []
        picker.colorChanged.connect(changed.append)
        sliders = _channel_sliders(dropdown)
        sliders[window.property("redChannel")].valueModified.emit(255)
        _pump(20)
        assert _rgb(dropdown.property("selectedColor")) == (255, 102, 153, 255)
        assert _rgb(picker.property("selectedColor")) == (255, 102, 153, 255)
        assert len(changed) == 1

        picker.setProperty("enableAlpha", False)
        _pump(20)
        assert not sliders[window.property("alphaChannel")].isVisible()
        assert _hex_input(dropdown).property("text") == "#ff6699"
        assert warnings == []
        assert _new_visible_windows(windows_before, window, popup_window) == []
    finally:
        _dispose_scene(engine, component, window, picker)


def test_color_picker_dropdown_accepts_rejects_and_closes_parent_popup(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, picker, warnings = _create_scene()
    try:
        accepted = []
        selected = []
        rejected = []
        picker.accepted.connect(accepted.append)
        picker.colorSelected.connect(selected.append)
        picker.rejected.connect(lambda: rejected.append(True))

        _popup_core_item, popup_window, dropdown = _open_dropdown(
            picker, window, windows_before
        )
        _click_item(
            popup_window,
            _action_button(dropdown, window.property("checkIcon")),
        )
        assert _wait_for(lambda: not picker.property("popupVisible"))
        assert _wait_for(lambda: not popup_window.isVisible())
        assert len(accepted) == 1
        assert len(selected) == 1
        assert _rgb(accepted[0]) == (51, 102, 153, 255)
        assert _rgb(selected[0]) == (51, 102, 153, 255)

        picker.setProperty("selectedColor", QColor("#445566"))
        _popup_core_item, popup_window, dropdown = _open_dropdown(
            picker, window, windows_before
        )
        _click_item(
            popup_window,
            _action_button(dropdown, window.property("dismissIcon")),
        )
        assert _wait_for(lambda: not picker.property("popupVisible"))
        assert _wait_for(lambda: not popup_window.isVisible())
        assert rejected == [True]
        assert _rgb(picker.property("selectedColor")) == (17, 34, 51, 255)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window, picker)


def test_color_picker_trigger_delegates_real_click_to_popup_menu(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, picker, warnings = _create_scene()
    try:
        trigger = _trigger_button(picker, window.property("dropdownFeature"))
        popup_core = _popup_core(picker)
        point = trigger.mapToScene(QPointF(trigger.width() / 2, trigger.height() / 2))
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            point.toPoint(),
        )
        assert _wait_for(lambda: picker.property("popupVisible"))
        assert _wait_for(lambda: popup_core.property("isOpen"))
        assert trigger.property("dropdownOpen")
        assert warnings == []
        assert _new_visible_windows(windows_before, window)
    finally:
        _dispose_scene(engine, component, window, picker)


def test_color_picker_dropdown_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        item for item in violations if item.rule in {"QML008", "QML009"}
    ] == []


def test_color_picker_dropdown_uses_mode_and_hex_tokens():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    for token in (
        "Enums.colorPickerMetrics.dropdownModeCycleStep",
        "Enums.colorPickerMetrics.dropdownModeCycleCount",
        "Enums.colorPickerMetrics.hexRadix",
        "Enums.colorPickerMetrics.hexPadCharacter",
        "Enums.opacityLevel.invisible",
    ):
        assert token in source
    for literal in (
        "colorMode + 1",
        ".toString(16)",
        ", 16)",
        ".padStart(Enums.colorPickerMetrics.hexByteLen, '0')",
    ):
        assert literal not in source
    assert source.count("selectionColor: Enums.accentColor") == source.count(
        "TextInput {"
    )
    assert source.count("selectedTextColor: Enums.accentForeground") == source.count(
        "TextInput {"
    )
