# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""AudioWaveform progress performance regressions. 音频波形进度性能回归。"""

from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QPoint,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QJSValue, QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "data"
    / "AudioWaveform.qml"
)
SCENE_SOURCE = b"""import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 360
    height: 120
    visible: true

    AudioWaveform {
        objectName: "waveform"
        x: 20
        y: 20
        width: 300
        height: 80
        waveformData: [0.2, 0.4, 0.6, 0.8]
        progress: 0.5
        animated: false
        showProgressIndicator: false
    }
}
"""
ANIMATED_SCENE_SOURCE = SCENE_SOURCE.replace(b"animated: false", b"animated: true")


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1_500) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _bars(waveform: QQuickItem) -> list[QQuickItem]:
    bars_parent = waveform.findChild(QQuickItem, "waveformBars")
    assert bars_parent is not None
    return sorted(
        [
            item
            for item in bars_parent.childItems()
            if "Rectangle" in item.metaObject().className()
        ],
        key=lambda item: item.x(),
    )


def _opacities(waveform: QQuickItem) -> list[float]:
    return [float(bar.opacity()) for bar in _bars(waveform)]


def _scale_values(waveform: QQuickItem) -> list[tuple[float, float]]:
    values = []
    for bar in _bars(waveform):
        scales = [
            child
            for child in bar.findChildren(QObject)
            if "Scale" in child.metaObject().className()
        ]
        assert len(scales) == 1
        values.append(
            (float(scales[0].property("xScale")), float(scales[0].property("yScale")))
        )
    return values


def _gradient(bar: QQuickItem) -> QObject:
    value = bar.property("gradient")
    assert isinstance(value, QJSValue)
    gradient = value.toQObject()
    assert gradient is not None
    return gradient


def _gradient_colors(bar: QQuickItem):
    gradient = _gradient(bar)
    stops = [
        child
        for child in gradient.findChildren(QObject)
        if "GradientStop" in child.metaObject().className()
    ]
    assert len(stops) == 2
    return [
        stop.property("color")
        for stop in sorted(stops, key=lambda stop: stop.property("position"))
    ]


def _create_scene(source: bytes = SCENE_SOURCE):
    engine = QQmlApplicationEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        source,
        QUrl.fromLocalFile(
            str(ROOT / "tests" / "qml" / "audio-waveform-progress-performance.qml")
        ),
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
    waveform = window.findChild(QQuickItem, "waveform")
    assert waveform is not None
    assert _wait_for(lambda: len(_bars(waveform)) == 4)
    return engine, component, window, waveform, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_audio_waveform_progress_preserves_bar_opacity_groups(qapp):
    engine, component, window, waveform, warnings = _create_scene()
    try:
        QTest.mouseMove(window, QPoint(350, 110))
        assert _wait_for(lambda: waveform.property("_hovered") is False)
        assert _opacities(waveform) == pytest.approx([1.0, 1.0, 0.7, 0.7])
        bars = _bars(waveform)
        assert _gradient_colors(bars[0]) == [
            waveform.property("progressColorEnd"),
            waveform.property("progressColor"),
        ]
        assert _gradient_colors(bars[2]) == [
            waveform.property("waveColorEnd"),
            waveform.property("waveColor"),
        ]
        gradient_pointers = [
            shiboken6.getCppPointer(_gradient(bar))[0] for bar in bars
        ]
        assert gradient_pointers[0] == gradient_pointers[1]
        assert gradient_pointers[2] == gradient_pointers[3]
        assert gradient_pointers[0] != gradient_pointers[2]

        waveform.setProperty("progress", 0.8)
        assert _wait_for(
            lambda: _opacities(waveform) == pytest.approx([1.0, 1.0, 1.0, 1.0])
        )
        assert _gradient_colors(bars[2]) == [
            waveform.property("progressColorEnd"),
            waveform.property("progressColor"),
        ]
        assert len({shiboken6.getCppPointer(_gradient(bar))[0] for bar in bars}) == 1

        waveform.setProperty("progress", 0.0)
        assert _wait_for(
            lambda: _opacities(waveform) == pytest.approx([0.7, 0.7, 0.7, 0.7])
        )
        assert _gradient_colors(bars[0]) == [
            waveform.property("waveColorEnd"),
            waveform.property("waveColor"),
        ]
        assert len({shiboken6.getCppPointer(_gradient(bar))[0] for bar in bars}) == 1
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_audio_waveform_bar_caches_position_and_played_state():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert source.count("_dataIndex / control._safeWaveformData.length") == 1
    assert "readonly property int _dataIndex:" in source
    assert "readonly property real _positionRatio:" in source
    assert "readonly property bool _played:" in source
    assert source.count("bar._played") == 2


def test_audio_waveform_hover_scale_preserves_curve_and_retargeting(qapp):
    engine, component, window, waveform, warnings = _create_scene(
        ANIMATED_SCENE_SOURCE
    )
    try:
        QTest.mouseMove(window, QPoint(350, 110))
        assert _wait_for(lambda: waveform.property("_hovered") is False)
        assert _scale_values(waveform) == pytest.approx([(1.0, 1.0)] * 4)

        QTest.mouseMove(window, QPoint(100, 50))
        assert _wait_for(lambda: waveform.property("_hovered") is True)
        _pump(30)
        entering = _scale_values(waveform)
        assert all(1.0 < x_scale < 1.05 for x_scale, _ in entering)
        assert entering == pytest.approx([entering[0]] * 4)
        assert (entering[0][0] - 1.0) / 0.05 == pytest.approx(
            (entering[0][1] - 1.0) / 0.02,
            abs=1e-4,
        )
        assert _wait_for(
            lambda: _scale_values(waveform) == pytest.approx([(1.05, 1.02)] * 4)
        )

        QTest.mouseMove(window, QPoint(350, 110))
        assert _wait_for(lambda: waveform.property("_hovered") is False)
        _pump(30)
        leaving = _scale_values(waveform)
        assert all(1.0 < x_scale < 1.05 for x_scale, _ in leaving)
        assert leaving == pytest.approx([leaving[0]] * 4)
        assert (leaving[0][0] - 1.0) / 0.05 == pytest.approx(
            (leaving[0][1] - 1.0) / 0.02,
            abs=1e-4,
        )
        assert _wait_for(
            lambda: _scale_values(waveform) == pytest.approx([(1.0, 1.0)] * 4)
        )
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_audio_waveform_dense_data_instantiates_only_visible_bars(qapp):
    engine, component, window, waveform, warnings = _create_scene()
    sample_count = 2_000
    values = [0.5 + ((index * 37) % 40) / 100 for index in range(sample_count)]
    try:
        waveform.setProperty("waveformData", values)
        bars_parent = waveform.findChild(QQuickItem, "waveformBars")
        assert bars_parent is not None
        assert _wait_for(
            lambda: len(_bars(waveform)) == bars_parent.property("_visibleCount")
        )
        bars = _bars(waveform)
        pitch = waveform.property("_safeBarWidth") + waveform.property(
            "_safeBarSpacing"
        )
        assert len(bars) <= waveform.width() / pitch + 2

        data_indices = [bar.property("_dataIndex") for bar in bars]
        assert all(isinstance(index, int) for index in data_indices)
        assert data_indices == list(range(data_indices[0], data_indices[-1] + 1))
        assert data_indices[0] > 0
        assert data_indices[-1] < sample_count - 1
        for bar, data_index in zip(bars, data_indices, strict=True):
            assert bar.x() == pytest.approx(data_index * pitch)
            expected_height = values[data_index] * bar.parentItem().height() * 0.9
            assert bar.height() == pytest.approx(expected_height)

        waveform.setWidth(200)
        assert _wait_for(
            lambda: len(_bars(waveform)) == bars_parent.property("_visibleCount")
        )
        narrow_indices = [bar.property("_dataIndex") for bar in _bars(waveform)]
        assert len(narrow_indices) < len(data_indices)
        assert narrow_indices[0] > data_indices[0]
        assert narrow_indices[-1] < data_indices[-1]
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
