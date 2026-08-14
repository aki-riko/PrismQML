# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Neumorphic color-picker input surface contracts. 新拟态颜色选择输入表面合同。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlProperty
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import Skin, Theme, getSkin, getTheme, register_types, setSkin, setTheme
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
INTERNAL_DIR = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "ColorPicker"
    / "_internal"
)
INTERNAL_URL = QUrl.fromLocalFile(str(INTERNAL_DIR)).toString()
SOURCE_PATHS = (
    INTERNAL_DIR / "ColorPickerInputs.qml",
    INTERNAL_DIR / "ColorPickerDropdown.qml",
    INTERNAL_DIR / "ColorPickerChannelSlider.qml",
    INTERNAL_DIR / "ColorPickerDialog.qml",
)
SCENE_SOURCE = f"""
import QtQuick
import QtQuick.Window
import PrismQML
import "{INTERNAL_URL}" as ColorPickerInternal

Window {{
    id: host
    width: 1100
    height: 760
    visible: true

    readonly property int expectedRadius: Enums.neumorphism.radius
    readonly property real expectedBorderWidth: Enums.neumorphism.borderWidth
    readonly property int inputsModeWidth: Enums.colorPickerMetrics.inputsModeWidth
    readonly property int dropdownModeWidth: Enums.colorPickerMetrics.dropdownModeWidth
    readonly property int compactInputHeight: Enums.controlSize.inputHeightCompact

    ColorPickerInternal.ColorPickerInputs {{
        id: inputs
        objectName: "neumorphicColorInputs"
        x: 40
        y: 40
        width: implicitWidth
        height: implicitHeight
    }}

    ColorPickerInternal.ColorPickerDropdown {{
        id: dropdown
        objectName: "neumorphicColorDropdown"
        x: 360
        y: 40
        width: implicitWidth
        height: implicitHeight
    }}

    ColorPickerInternal.ColorPickerDialog {{
        id: dialog
        objectName: "neumorphicColorDialog"
        overlayTarget: host.contentItem
    }}
}}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1000) -> bool:
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
        item = pending.pop()
        result.append(item)
        pending.extend(item.childItems())
    return result


def _text_input_surfaces(root: QQuickItem) -> list[QQuickItem]:
    surfaces = []
    for item in _visual_descendants(root):
        if not item.metaObject().className().startswith("QQuickTextInput"):
            continue
        surface = item.parentItem()
        assert surface is not None
        assert surface.metaObject().className().startswith("QQuickRectangle")
        surfaces.append(surface)
    return surfaces


def _mode_surface(root: QQuickItem, width: int, height: int) -> QQuickItem:
    matches = [
        item.parentItem()
        for item in _visual_descendants(root)
        if item.metaObject().className().startswith("QQuickMouseArea")
        and item.parentItem() is not None
        and item.parentItem().width() == width
        and item.parentItem().height() == height
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _matching_shadows(scope: QQuickWindow, target: QObject) -> list[QQuickItem]:
    return [
        child
        for child in _visual_descendants(scope.contentItem())
        if child.metaObject().indexOfProperty("target") >= 0
        and child.metaObject().indexOfProperty("inset") >= 0
        and child.metaObject().indexOfProperty("pressed") >= 0
        and child.metaObject().indexOfProperty("darkColor") >= 0
        and child.metaObject().indexOfProperty("lightColor") >= 0
        and child.property("target") == target
    ]


def _border_width(item: QObject, engine) -> float:
    return float(QQmlProperty(item, "border.width", engine).read())


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        SCENE_SOURCE.encode("utf-8"),
        QUrl("inline:neumorphism-color-picker-surfaces.qml"),
    )
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
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def test_color_picker_control_surfaces_use_neumorphic_geometry_and_shadows(qapp):
    previous_skin = getSkin()
    previous_theme = getTheme()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    setTheme(Theme.LIGHT)
    setSkin(Skin.NEUMORPHISM)
    engine, component, window, warnings = _create_scene()
    try:
        inputs = window.findChild(QQuickItem, "neumorphicColorInputs")
        dropdown = window.findChild(QQuickItem, "neumorphicColorDropdown")
        dialog = window.findChild(QQuickItem, "neumorphicColorDialog")
        assert inputs is not None and dropdown is not None and dialog is not None

        expected_radius = window.property("expectedRadius")
        expected_border = window.property("expectedBorderWidth")
        input_surfaces = _text_input_surfaces(inputs)
        dropdown_surfaces = _text_input_surfaces(dropdown)
        dialog_surfaces = _text_input_surfaces(dialog)
        assert len(input_surfaces) == 4
        assert len(dropdown_surfaces) == 5
        assert len(dialog_surfaces) == 4

        all_input_surfaces = input_surfaces + dropdown_surfaces + dialog_surfaces
        for surface in all_input_surfaces:
            assert surface.property("radius") == expected_radius
            assert _border_width(surface, engine) == expected_border
            shadows = _matching_shadows(window, surface)
            assert len(shadows) == 1
            assert shadows[0].property("inset") is True

        mode_surfaces = (
            _mode_surface(
                inputs,
                window.property("inputsModeWidth"),
                window.property("compactInputHeight"),
            ),
            _mode_surface(
                dropdown,
                window.property("dropdownModeWidth"),
                window.property("compactInputHeight"),
            ),
        )
        for surface in mode_surfaces:
            assert surface.property("radius") == expected_radius
            assert _border_width(surface, engine) == expected_border
            shadows = _matching_shadows(window, surface)
            assert len(shadows) == 1
            assert shadows[0].property("inset") is False

        text_inputs = [
            item
            for item in _visual_descendants(inputs)
            if item.metaObject().className().startswith("QQuickTextInput")
        ]
        text_inputs[0].forceActiveFocus()
        _pump()
        assert text_inputs[0].property("activeFocus") is True
        assert _border_width(text_inputs[0].parentItem(), engine) == expected_border

        assert warnings == []
        assert [
            item
            for item in QGuiApplication.topLevelWindows()
            if item.isVisible() and item not in windows_before and item is not window
        ] == []
    finally:
        _dispose_scene(engine, component, window)
        setTheme(previous_theme)
        setSkin(previous_skin)


def test_color_picker_surface_sources_follow_qml_conventions():
    for source_path in SOURCE_PATHS:
        source = source_path.read_text(encoding="utf-8")
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations = scan_source_text(source, path)
        assert [
            violation
            for violation in violations
            if violation.rule in {"QML008", "QML009"}
        ] == []
