# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Remaining numeric and nullable-input regressions. 其余数值与可空输入回归。"""

import math
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SLIDER_CASES = (
    (
        ROOT / "prismqml" / "PrismQML" / "controls" / "inputs" / "ColorPicker" / "GradientSlider.qml",
        "value",
        2,
        "_safeValue",
        1,
    ),
    (
        ROOT / "prismqml" / "PrismQML" / "controls" / "inputs" / "ColorPicker" / "_internal" / "ColorPickerBrightnessSlider.qml",
        "value",
        -2,
        "_safeValue",
        0,
    ),
    (
        ROOT / "prismqml" / "PrismQML" / "controls" / "inputs" / "ColorPicker" / "_internal" / "ColorPickerHueSlider.qml",
        "value",
        2,
        "_safeValue",
        1,
    ),
    (
        ROOT / "prismqml" / "PrismQML" / "controls" / "inputs" / "ColorPicker" / "_internal" / "ColorPickerChannelSlider.qml",
        "value",
        999,
        "_safeValue",
        255,
    ),
    (
        ROOT / "prismqml" / "PrismQML" / "controls" / "inputs" / "Slider" / "BeforeAfterSlider.qml",
        "position",
        2,
        "_safePosition",
        1,
    ),
)


SCENE = b"""
import QtQuick
import PrismQML

Item {
    PipsPager {
        objectName: "pips"
        pageCount: -3
        currentIndex: -2
        visiblePipCount: 0
    }

    Marquee {
        objectName: "marquee"
        width: 0
        text: "edge"
        forceScroll: true
        speed: 0
        scrollGap: -5
    }

    AudioWaveform {
        objectName: "waveform"
        width: 0
        height: 0
        waveformData: [null, 2, -1]
        progress: 2
    }

    Stepper {
        objectName: "stepper"
        steps: [null, {text: "Done"}]
        currentStep: 99
    }

    ChartDataZoom {
        objectName: "dataZoom"
        width: 0
        height: 0
        chartData: [null, {value: "bad"}, {value: 3}]
        series: [null]
        viewportStart: -2
        viewportEnd: 2
    }

    SliderCore {
        objectName: "slider"
        readonly property real testedPosition: _safePosition(value)
        width: 0
        height: 0
        value: 50
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _visual_tree(root: QQuickItem) -> list[QQuickItem]:
    result = [root]
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def test_nullable_lists_and_zero_geometry_stay_finite(qapp):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE, QUrl("inline:remaining-numeric-robustness.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    try:
        _pump()
        pips = root.findChild(type(root), "pips")
        marquee = root.findChild(type(root), "marquee")
        waveform = root.findChild(type(root), "waveform")
        stepper = root.findChild(type(root), "stepper")
        data_zoom = root.findChild(type(root), "dataZoom")
        slider = root.findChild(type(root), "slider")
        assert pips is not None and marquee is not None
        assert waveform is not None and stepper is not None and data_zoom is not None
        assert slider is not None

        assert pips.property("_safePageCount") == 0
        assert pips.property("_safeVisiblePipCount") == 1
        assert pips.property("_safeCurrentIndex") == 0

        assert marquee.property("_safeSpeed") == 1
        assert marquee.property("_safeScrollGap") == 0
        assert math.isfinite(float(marquee.property("_scrollDuration")))

        assert waveform.property("_safeWaveformData").toVariant() == [0, 1, 0]
        assert waveform.property("_safeProgress") == 1

        assert stepper.property("_safeSteps").toVariant() == [None, {"text": "Done"}]
        assert stepper.property("_safeCurrentStep") == 1
        assert math.isfinite(float(stepper.property("_lineWidth")))

        assert data_zoom.property("_safeViewportStart") == 0
        assert data_zoom.property("_safeViewportEnd") == 1
        assert slider.property("testedPosition") == 0.5
        assert warnings == []
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()


def test_zero_width_slider_variants_keep_finite_geometry(qapp):
    for source_path, value_name, value, safe_name, expected in SLIDER_CASES:
        engine = QQmlApplicationEngine()
        warnings = []
        engine.warnings.connect(
            lambda errors: warnings.extend(error.toString() for error in errors)
        )
        register_types(engine)
        component = QQmlComponent(engine, QUrl.fromLocalFile(str(source_path)))
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        slider = component.create(engine.rootContext())
        assert isinstance(slider, QQuickItem), [
            error.toString() for error in component.errors()
        ]
        try:
            slider.setWidth(0)
            slider.setProperty(value_name, value)
            _pump()
            assert slider.property(safe_name) == expected
            assert all(
                math.isfinite(number)
                for item in _visual_tree(slider)
                for number in (item.x(), item.y(), item.width(), item.height())
            )
            assert warnings == []
        finally:
            slider.deleteLater()
            component.deleteLater()
            engine.collectGarbage()
            engine.clearComponentCache()
            engine.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            QCoreApplication.processEvents()
