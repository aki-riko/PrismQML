# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Color picker circle async-width regression. 圆形颜色选择器异步宽度回归。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types
from prismqml.python.core.incubation import install_incubation_controller
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "ColorPicker"
    / "ColorPicker.qml"
)
CONTENT_SOURCE_PATH = SOURCE_PATH.parent / "_internal" / "ColorPickerContent.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "color-picker-circle-async-width.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property bool asyncReady: asyncLoader.item !== null
    readonly property real asyncWidth: asyncLoader.item
        ? asyncLoader.item.implicitWidth
        : -1
    readonly property real syncWidth: syncPicker.implicitWidth

    width: 400
    height: 100
    visible: true

    ColorPicker {
        id: syncPicker
        type: Enums.colorPicker.type_circle
    }

    Loader {
        id: asyncLoader
        asynchronous: true
        sourceComponent: ColorPicker {
            type: Enums.colorPicker.type_circle
        }
    }
}
"""


def _pump(milliseconds: int = 5) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _new_visible_windows(windows_before, root_window):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and window is not root_window
        and not any(window is existing for existing in windows_before)
    ]


def test_public_circle_async_loader_preserves_runtime_width(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    controller = install_incubation_controller(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    try:
        root.requestActivate()
        for _ in range(80):
            controller.incubateFor(5)
            _pump()
            if (
                root.property("asyncReady")
                and root.property("asyncWidth") == pytest.approx(
                    root.property("syncWidth")
                )
            ):
                break
        assert root.property("asyncReady")
        assert root.property("syncWidth") == pytest.approx(276)
        assert root.property("asyncWidth") == pytest.approx(276)
        assert warnings == []
        assert _new_visible_windows(windows_before, root) == []
    finally:
        root.close()
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        qapp.processEvents()


def test_public_color_picker_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    content_source = CONTENT_SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    content_path = PurePosixPath(CONTENT_SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path) + scan_source_text(
        content_source, content_path
    )
    assert [
        item for item in violations if item.rule in {"QML008", "QML009"}
    ] == []


def test_public_color_picker_uses_circle_and_popup_tokens():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    content_source = CONTENT_SOURCE_PATH.read_text(encoding="utf-8")
    combined_source = source + content_source
    for token in (
        "Enums.colorPickerMetrics.circleLoaderFallbackWidth",
        "Enums.colorPickerMetrics.circleDefaultSize",
        "Enums.colorPickerMetrics.palettePopupWidth",
        "Enums.colorPickerMetrics.pickerPopupWidth",
        "Enums.colorPickerMetrics.fallbackPopupWidth",
        "Enums.colorPickerMetrics.palettePopupHeight",
        "Enums.colorPickerMetrics.pickerPopupHeight",
        "Enums.colorPickerMetrics.fallbackPopupHeight",
    ):
        assert token in combined_source
    assert (
        "circleLoader.item ? circleLoader.item.implicitWidth "
        ": circleLoader.item.implicitWidth"
    ) not in source
