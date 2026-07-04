# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design auxiliary data and media skin tests."""

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, register_types, setSkin, setTheme


def _build(engine, qml: bytes):
    component = QQmlComponent(engine)
    component.setData(qml, QUrl("inline"))
    assert not component.isError(), [error.toString() for error in component.errors()]

    item = component.create(engine.rootContext())
    assert item is not None, [error.toString() for error in component.errors()]
    return component, item


def _rgb(qcolor):
    return (
        round(qcolor.redF() * 255),
        round(qcolor.greenF() * 255),
        round(qcolor.blueF() * 255),
    )


def _alpha(qcolor):
    return round(qcolor.alphaF() * 255)


def _rgba(qcolor):
    return (
        round(qcolor.redF() * 255),
        round(qcolor.greenF() * 255),
        round(qcolor.blueF() * 255),
        round(qcolor.alphaF() * 255),
    )


def _assert_stepper(item, active, inactive, border, on_active, inactive_text, active_label):
    assert _rgb(item.property("_stepActiveColor")) == active
    assert _rgb(item.property("_stepInactiveColor")) == inactive
    assert _rgb(item.property("_stepBorderColor")) == border
    assert _rgb(item.property("_stepActiveContentColor")) == on_active
    assert _rgb(item.property("_stepInactiveContentColor")) == inactive_text
    assert _rgb(item.property("_stepActiveLabelColor")) == active_label


def _assert_gauge(item, track, value, label):
    assert _rgb(item.property("_gaugeTrackColor")) == track
    assert _rgb(item.property("_gaugeValueColor")) == value
    assert _rgb(item.property("_gaugeLabelColor")) == label
    assert item.property("_gaugeStrokeWidth") == 12


def _assert_indicator(item, active, inactive):
    assert _rgb(item.property("_indicatorActiveColor")) == active
    assert _rgb(item.property("_indicatorInactiveColor")) == inactive


def _assert_audio(item, border, overlay):
    assert item.property("_waveformRadius") == 8
    assert item.property("_waveformInnerRadius") == 6
    assert _rgb(item.property("_waveformBorderColor")) == border
    assert _rgb(item.property("_progressOverlayColor")) == overlay
    assert _alpha(item.property("_progressOverlayColor")) == 26


def _assert_image_widget(item, placeholder, icon):
    assert item.property("radius") == 6
    assert _rgb(item.property("_placeholderColor")) == placeholder
    assert _rgb(item.property("_placeholderIconColor")) == icon


def _assert_qr_code(item, border, hint):
    assert item.property("_qrPlaceholderRadius") == 6
    assert _rgb(item.property("_qrBorderColor")) == border
    assert _rgb(item.property("_qrHintColor")) == hint


def _assert_avatar(item, border, content):
    assert item.property("_avatarBorderWidth") == 1
    assert _rgb(item.property("_avatarBorderColor")) == border
    assert _rgb(item.property("_avatarContentColor")) == content


def test_prism_design_auxiliary_data_components_light_and_dark(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build(engine, b"""
import PrismQML
Badge {
    count: 7
    level: Enums.statusLevel.success
}
"""))
        badge = keep[-1][1]
        assert _rgb(badge.property("_contentColor")) == (255, 255, 255)

        keep.append(_build(engine, b"""
import PrismQML
Stepper {
    width: 360
    steps: ["Draft", "Review", "Ship"]
    currentStep: 1
}
"""))
        stepper = keep[-1][1]
        _assert_stepper(
            stepper,
            (47, 111, 237),
            (255, 255, 255),
            (217, 227, 236),
            (255, 255, 255),
            (95, 111, 128),
            (23, 32, 42),
        )

        keep.append(_build(engine, b"""
import PrismQML
CircularGauge {
    value: 42
    unit: "%"
}
"""))
        gauge = keep[-1][1]
        _assert_gauge(gauge, (234, 241, 247), (47, 111, 237), (131, 146, 164))

        keep.append(_build(engine, b"""
import PrismQML
IndicatorBar {
    active: true
}
"""))
        indicator = keep[-1][1]
        _assert_indicator(indicator, (47, 111, 237), (170, 184, 199))
        assert indicator.property("animationDuration") == 200

        keep.append(_build(engine, b"""
import PrismQML
AudioWaveform {
    width: 240
    height: 80
    waveformData: [0.2, 0.5, 0.8]
    progress: 0.4
}
"""))
        audio = keep[-1][1]
        _assert_audio(audio, (231, 238, 245), (47, 111, 237))

        keep.append(_build(engine, b"""
import PrismQML
ImageWidget {
    width: 96
    height: 64
}
"""))
        image_widget = keep[-1][1]
        _assert_image_widget(image_widget, (238, 245, 255), (47, 111, 237))

        keep.append(_build(engine, b"""
import PrismQML
QRCode {
    content: ""
}
"""))
        qr_code = keep[-1][1]
        _assert_qr_code(qr_code, (217, 227, 236), (95, 111, 128))

        keep.append(_build(engine, b"""
import PrismQML
Avatar {
    text: "Prism"
}
"""))
        avatar = keep[-1][1]
        _assert_avatar(avatar, (170, 184, 199), (255, 255, 255))

        keep.append(_build(engine, b"""
import PrismQML
DataWidgetCore {
    width: 240
    height: 140
    showHeader: true
}
"""))
        data_widget = keep[-1][1]
        assert _rgba(data_widget.property("_headerEdgeShadowColor")) == (10, 26, 42, 20)

        setTheme(Theme.DARK)
        keep.append(_build(engine, b"""
import PrismQML
Badge {
    count: 7
    level: Enums.statusLevel.success
}
"""))
        dark_badge = keep[-1][1]
        assert _rgb(dark_badge.property("_contentColor")) == (15, 23, 42)

        keep.append(_build(engine, b"""
import PrismQML
Stepper {
    width: 360
    steps: ["Draft", "Review", "Ship"]
    currentStep: 1
}
"""))
        dark_stepper = keep[-1][1]
        _assert_stepper(
            dark_stepper,
            (122, 167, 255),
            (32, 38, 46),
            (48, 58, 70),
            (15, 23, 42),
            (166, 177, 191),
            (238, 243, 248),
        )

        keep.append(_build(engine, b"""
import PrismQML
CircularGauge {
    value: 42
    unit: "%"
}
"""))
        dark_gauge = keep[-1][1]
        _assert_gauge(dark_gauge, (21, 26, 32), (122, 167, 255), (118, 131, 148))

        keep.append(_build(engine, b"""
import PrismQML
IndicatorBar {
    active: true
}
"""))
        dark_indicator = keep[-1][1]
        _assert_indicator(dark_indicator, (122, 167, 255), (75, 90, 107))

        keep.append(_build(engine, b"""
import PrismQML
AudioWaveform {
    width: 240
    height: 80
    waveformData: [0.2, 0.5, 0.8]
    progress: 0.4
}
"""))
        dark_audio = keep[-1][1]
        _assert_audio(dark_audio, (38, 48, 58), (122, 167, 255))

        keep.append(_build(engine, b"""
import PrismQML
ImageWidget {
    width: 96
    height: 64
}
"""))
        dark_image_widget = keep[-1][1]
        _assert_image_widget(dark_image_widget, (38, 48, 58), (122, 167, 255))

        keep.append(_build(engine, b"""
import PrismQML
QRCode {
    content: ""
}
"""))
        dark_qr_code = keep[-1][1]
        _assert_qr_code(dark_qr_code, (48, 58, 70), (166, 177, 191))

        keep.append(_build(engine, b"""
import PrismQML
Avatar {
    text: "Prism"
}
"""))
        dark_avatar = keep[-1][1]
        _assert_avatar(dark_avatar, (75, 90, 107), (15, 23, 42))

        keep.append(_build(engine, b"""
import PrismQML
DataWidgetCore {
    width: 240
    height: 140
    showHeader: true
}
"""))
        dark_data_widget = keep[-1][1]
        assert _rgba(dark_data_widget.property("_headerEdgeShadowColor")) == (0, 0, 0, 68)
    finally:
        for component, item in reversed(keep):
            item.deleteLater()
            component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        qapp.processEvents()
        setTheme(Theme.LIGHT)
        setSkin(Skin.FLUENT)
