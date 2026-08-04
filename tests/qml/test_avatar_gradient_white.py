# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Avatar and gradient fixed-white runtime regressions. 固定白色运行时回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QEventLoop, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlProperty

from prismqml import Skin, Theme, register_types, setSkin, setTheme


ROOT = Path(__file__).resolve().parents[2]
AVATAR_SELECTOR_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "data"
    / "Avatar"
    / "AvatarSelector.qml"
)
GRADIENT_SLIDER_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "ColorPicker"
    / "GradientSlider.qml"
)
COLOR_PICKER_PANEL_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "ColorPicker"
    / "_internal"
    / "ColorPickerPanel.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "avatar-gradient-white.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML
import "../../prismqml/PrismQML/controls/inputs/ColorPicker/_internal"

Item {
    id: root

    readonly property color defaultWhite: defaultRectangle.color
    readonly property color fixedWhite: Enums.themeColors.accentForeground
    readonly property var cameraIcon: Enums.icon.camera
    readonly property int borderNormal: Enums.border.normal
    readonly property int lightnessMode: Enums.gradientSlider.mode_lightness

    width: 320
    height: 180

    Rectangle {
        id: defaultRectangle
        visible: false
    }

    AvatarSelector {
        objectName: "avatarSelector"
        size: 64
        changeText: "Change"
    }

    GradientSlider {
        objectName: "gradientSlider"
        y: 100
        width: 200
        value: 0.25
    }

    ColorPickerPanel {
        objectName: "colorPickerPanel"
        x: 340
        width: 260
        height: 200
    }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
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
    _pump(1)
    return engine, component, root


def _walk_visual_tree(root: QQuickItem):
    stack = [root]
    while stack:
        item = stack.pop()
        yield item
        stack.extend(reversed(item.childItems()))


def _find_unique(root: QQuickItem, predicate, label: str) -> QQuickItem:
    matches = [item for item in _walk_visual_tree(root) if predicate(item)]
    assert len(matches) == 1, (
        label,
        [
            (
                item.metaObject().className(),
                item.x(),
                item.y(),
                item.width(),
                item.height(),
            )
            for item in matches
        ],
    )
    return matches[0]


def _read(item: QQuickItem, name: str):
    prop = QQmlProperty(item, name)
    assert prop.isValid(), (item.metaObject().className(), name)
    return prop.read()


def _assert_color(actual: QColor, expected: QColor) -> None:
    actual_channels = (actual.redF(), actual.greenF(), actual.blueF(), actual.alphaF())
    expected_channels = (
        expected.redF(),
        expected.greenF(),
        expected.blueF(),
        expected.alphaF(),
    )
    assert actual_channels == pytest.approx(expected_channels, abs=1 / 65535)


def _avatar_foregrounds(
    avatar: QQuickItem, camera_icon
) -> tuple[QQuickItem, QQuickItem]:
    camera = _find_unique(
        avatar,
        lambda item: item.metaObject().indexOfProperty("icon") >= 0
        and item.property("icon") == camera_icon,
        "avatar camera icon",
    )
    change_text = _find_unique(
        avatar,
        lambda item: item.metaObject().indexOfProperty("text") >= 0
        and item.property("text") == "Change",
        "avatar change label",
    )
    return camera, change_text


def _gradient_handle(gradient: QQuickItem) -> QQuickItem:
    return _find_unique(
        gradient,
        lambda item: item.metaObject().className() == "QQuickRectangle"
        and item.width() == pytest.approx(20)
        and item.height() == pytest.approx(20)
        and item.property("radius") == pytest.approx(10),
        "gradient slider handle",
    )


def _gradient_stops(gradient: QQuickItem):
    stops = [
        item
        for item in gradient.findChildren(QObject)
        if item.metaObject().indexOfProperty("position") >= 0
        and item.metaObject().indexOfProperty("color") >= 0
        and "GradientStop" in item.metaObject().className()
    ]
    assert len(stops) == 7, [item.metaObject().className() for item in stops]
    return sorted(stops, key=lambda item: item.property("position"))


def _color_picker_selector(panel: QQuickItem) -> QQuickItem:
    return _find_unique(
        panel,
        lambda item: item.metaObject().indexOfProperty("radius") >= 0
        and item.width() == pytest.approx(16)
        and item.height() == pytest.approx(16),
        "color picker selector",
    )


def _assert_gradient_palette(root: QQuickItem) -> None:
    gradient = root.findChild(QQuickItem, "gradientSlider")
    expected_positions = (0.0, 0.166, 0.333, 0.5, 0.666, 0.833, 1.0)
    expected_colors = ("red", "yellow", "lime", "cyan", "blue", "magenta", "red")
    for stop, position, color in zip(
        _gradient_stops(gradient), expected_positions, expected_colors
    ):
        assert stop.property("position") == pytest.approx(position)
        _assert_color(stop.property("color"), QColor(color))

    gradient.setProperty("mode", root.property("lightnessMode"))
    lightness = _gradient_stops(gradient)
    for index, color in ((0, "black"), (3, "gray"), (6, "white")):
        _assert_color(lightness[index].property("color"), QColor(color))


def _assert_selector_contrast(root: QQuickItem) -> None:
    panel = root.findChild(QQuickItem, "colorPickerPanel")
    selector = _color_picker_selector(panel)
    panel.setProperty("brightness", 1.0)
    panel.setProperty("saturation", 0.0)
    _assert_color(_read(selector, "border.color"), QColor("black"))
    panel.setProperty("brightness", 0.0)
    panel.setProperty("saturation", 1.0)
    _assert_color(_read(selector, "border.color"), QColor("white"))


def _assert_fixed_white(root: QQuickItem) -> None:
    expected = root.property("fixedWhite")
    default_white = root.property("defaultWhite")
    _assert_color(expected, QColor("white"))
    _assert_color(default_white, expected)

    avatar = root.findChild(QQuickItem, "avatarSelector")
    gradient = root.findChild(QQuickItem, "gradientSlider")
    assert avatar is not None and gradient is not None
    camera, change_text = _avatar_foregrounds(avatar, root.property("cameraIcon"))
    handle = _gradient_handle(gradient)

    _assert_color(camera.property("color"), expected)
    _assert_color(change_text.property("color"), expected)
    _assert_color(handle.property("color"), default_white)
    assert gradient.width() == pytest.approx(200)
    assert gradient.height() == pytest.approx(24)
    assert handle.x() == pytest.approx(45)
    assert handle.y() == pytest.approx(2)
    assert _read(handle, "border.width") == root.property("borderNormal")


def test_avatar_and_gradient_preserve_fixed_white_runtime(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.FLUENT)
    engine, component, root = _create_scene()
    try:
        for theme, skin in (
            (Theme.LIGHT, Skin.FLUENT),
            (Theme.DARK, Skin.FLUENT),
            (Theme.DARK, Skin.NEOBRUTALISM),
        ):
            setTheme(theme)
            setSkin(skin)
            _pump(5)
            _assert_fixed_white(root)
    finally:
        setSkin(Skin.FLUENT)
        setTheme(Theme.LIGHT)
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_avatar_selector_defers_and_reuses_dialogs(qapp):
    engine, component, root = _create_scene()
    try:
        avatar = root.findChild(QQuickItem, "avatarSelector")
        assert avatar is not None
        assert avatar.property("_fileDialog") is None
        assert avatar.property("_cropperDialog") is None

        file_dialog = avatar._ensureFileDialog()
        cropper_dialog = avatar._ensureCropperDialog()
        assert file_dialog is not None
        assert cropper_dialog is not None
        assert file_dialog.parent() == avatar
        assert cropper_dialog.parent() == avatar
        assert avatar._ensureFileDialog() == file_dialog
        assert avatar._ensureCropperDialog() == cropper_dialog
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_color_picker_preserves_fixed_gradient_palette(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.FLUENT)
    engine, component, root = _create_scene()
    try:
        _assert_gradient_palette(root)
        _assert_selector_contrast(root)
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_avatar_and_gradient_sources_use_fixed_white_contracts():
    avatar_source = AVATAR_SELECTOR_SOURCE.read_text(encoding="utf-8")
    gradient_source = GRADIENT_SLIDER_SOURCE.read_text(encoding="utf-8")
    panel_source = COLOR_PICKER_PANEL_SOURCE.read_text(encoding="utf-8")

    assert avatar_source.count("color: Enums.themeColors.accentForeground") == 2
    assert 'color: "white"' not in avatar_source

    handle_props = gradient_source.split("id: handle", 1)[1].split(
        "Rectangle {", 1
    )[0]
    assert not any(
        line.strip().startswith("color:") for line in handle_props.splitlines()
    )
    for index in range(7):
        assert f"Enums.colorPickerGradient.huePos{index}" in gradient_source
        assert f"Enums.colorPickerGradient.hueColor{index}" in gradient_source
    for token in ("lightnessDark", "lightnessMid", "lightnessLight"):
        assert f"Enums.colorPickerGradient.{token}" in gradient_source
    assert "Enums.colorPickerGradient.lightnessDark" in panel_source
    assert "Enums.colorPickerGradient.lightnessLight" in panel_source
    for name in ("red", "yellow", "lime", "cyan", "blue", "magenta", "black", "gray", "white"):
        assert f'"{name}"' not in gradient_source
