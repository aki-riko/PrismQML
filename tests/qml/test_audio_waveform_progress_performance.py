# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""AudioWaveform progress performance regressions. 音频波形进度性能回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QPoint,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
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
    rows = [
        item
        for item in waveform.findChildren(QQuickItem)
        if "QQuickRow" in item.metaObject().className()
    ]
    assert len(rows) == 1
    return sorted(
        [
            item
            for item in rows[0].childItems()
            if "Rectangle" in item.metaObject().className()
        ],
        key=lambda item: item.x(),
    )


def _opacities(waveform: QQuickItem) -> list[float]:
    return [float(bar.opacity()) for bar in _bars(waveform)]


def _gradient_colors(bar: QQuickItem):
    stops = [
        child
        for child in bar.findChildren(QObject)
        if "GradientStop" in child.metaObject().className()
    ]
    assert len(stops) == 2
    return [
        stop.property("color")
        for stop in sorted(stops, key=lambda stop: stop.property("position"))
    ]


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        SCENE_SOURCE,
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

        waveform.setProperty("progress", 0.8)
        assert _wait_for(
            lambda: _opacities(waveform) == pytest.approx([1.0, 1.0, 1.0, 1.0])
        )
        assert _gradient_colors(bars[2]) == [
            waveform.property("progressColorEnd"),
            waveform.property("progressColor"),
        ]

        waveform.setProperty("progress", 0.0)
        assert _wait_for(
            lambda: _opacities(waveform) == pytest.approx([0.7, 0.7, 0.7, 0.7])
        )
        assert _gradient_colors(bars[0]) == [
            waveform.property("waveColorEnd"),
            waveform.property("waveColor"),
        ]
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_audio_waveform_bar_caches_position_and_played_state():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert source.count("index / control._safeWaveformData.length") == 1
    assert "readonly property real _positionRatio:" in source
    assert "readonly property bool _played:" in source
    assert source.count("bar._played") == 3
