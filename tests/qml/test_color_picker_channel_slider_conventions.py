# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Color picker channel slider regressions. 颜色通道滑块回归。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

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
    / "ColorPickerChannelSlider.qml"
)
ANIMATION_SETTLE_MS = 150  # Enums.duration.fast (100 ms) plus event-loop margin 动画时长加事件循环余量


def _descendants(root: QObject) -> list[QObject]:
    result = []
    pending = list(root.children())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.children())
    return result


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def _create_slider(qapp):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(SOURCE_PATH)))
    assert not component.isError(), [error.toString() for error in component.errors()]
    slider = component.create(engine.rootContext())
    assert isinstance(slider, QQuickItem)
    slider.setWidth(slider.property("implicitWidth"))
    slider.setHeight(slider.property("implicitHeight"))
    qapp.processEvents()
    return engine, component, slider, warnings


def _gradient_stops(slider: QQuickItem) -> list[QObject]:
    stops = [
        child
        for child in _descendants(slider)
        if child.metaObject().indexOfProperty("position") >= 0
        and child.metaObject().indexOfProperty("color") >= 0
    ]
    return sorted(stops, key=lambda stop: stop.property("position"))


def _rgba(color: QColor) -> tuple[float, float, float, float]:
    return tuple(round(value, 4) for value in color.getRgbF())


def _new_visible_windows(windows_before):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
    ]


def _pump(milliseconds: int) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def test_channel_slider_preserves_geometry_and_handle_range(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, slider, warnings = _create_slider(qapp)
    try:
        assert slider.property("implicitWidth") == pytest.approx(260)
        assert slider.property("implicitHeight") == pytest.approx(24)
        handles = [
            item
            for item in _visual_descendants(slider)
            if item.width() == pytest.approx(16)
            and item.height() == pytest.approx(16)
        ]
        assert len(handles) == 1
        handle = handles[0]
        assert handle.x() == pytest.approx(0)
        slider.setProperty("value", 255)
        _pump(ANIMATION_SETTLE_MS)
        assert handle.x() == pytest.approx(handle.parentItem().width() - handle.width())
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        slider.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        qapp.processEvents()


def test_channel_slider_preserves_four_channel_gradients(qapp):
    engine, component, slider, warnings = _create_slider(qapp)
    try:
        slider.setProperty("baseColor", QColor.fromRgbF(0.25, 0.5, 0.75, 0.8))
        expected = {
            0: ((0.0, 0.5, 0.75, 1.0), (1.0, 0.5, 0.75, 1.0)),
            1: ((0.25, 0.0, 0.75, 1.0), (0.25, 1.0, 0.75, 1.0)),
            2: ((0.25, 0.5, 0.0, 1.0), (0.25, 0.5, 1.0, 1.0)),
            3: ((0.25, 0.5, 0.75, 0.0), (0.25, 0.5, 0.75, 1.0)),
        }
        stops = _gradient_stops(slider)
        assert len(stops) == 2
        for channel, colors in expected.items():
            slider.setProperty("channel", channel)
            qapp.processEvents()
            assert _rgba(stops[0].property("color")) == pytest.approx(colors[0])
            assert _rgba(stops[1].property("color")) == pytest.approx(colors[1])
        assert warnings == []
    finally:
        slider.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        qapp.processEvents()


def test_channel_slider_uses_tokens_and_convention_order():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        item for item in violations if item.rule in {"QML008", "QML009"}
    ] == []
    for token in (
        "Enums.colorPickerMetrics.channelMinValue",
        "Enums.colorPickerMetrics.channelMaxValue",
        "Enums.colorPickerMetrics.dialogRgbChannelR",
        "Enums.colorPickerMetrics.dialogRgbChannelG",
        "Enums.colorPickerMetrics.dialogRgbChannelB",
        "Enums.colorPickerMetrics.channelAlphaIndex",
        "Enums.colorPickerMetrics.checkerboardParity",
        "Enums.opacityLevel.invisible",
        "Enums.opacityLevel.visible",
    ):
        assert token in source
    for literal in (
        "property int channel: 0",
        "property int value: 0",
        "bottom: 0",
        "case 0:",
        "case 1:",
        "case 2:",
        "case 3:",
        "% 2 === 0",
    ):
        assert literal not in source
