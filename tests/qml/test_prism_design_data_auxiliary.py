# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design auxiliary data and media skin tests."""

from pathlib import Path

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


def _assert_indicator(item, active, inactive, inactive_gradient_alpha=64):
    assert _rgb(item.property("_indicatorActiveColor")) == active
    assert _rgb(item.property("_indicatorInactiveColor")) == inactive
    assert item.property("_inactiveGradientAlpha") == 0.25
    assert _alpha(item.property("_bottomColor")) == inactive_gradient_alpha


def _assert_audio(item, border, overlay):
    assert item.property("_waveformRadius") == 6
    assert item.property("_waveformInnerRadius") == 4
    assert _rgb(item.property("_waveformBorderColor")) == border
    assert _rgb(item.property("_progressOverlayColor")) == overlay
    assert _alpha(item.property("_progressOverlayColor")) == 26


def _assert_image_widget(item, placeholder, icon):
    assert item.property("radius") == 4
    assert _rgb(item.property("_placeholderColor")) == placeholder
    assert _rgb(item.property("_placeholderIconColor")) == icon


def _assert_qr_code(item, border, hint):
    assert item.property("_qrPlaceholderRadius") == 4
    assert _rgb(item.property("_qrBorderColor")) == border
    assert _rgb(item.property("_qrHintColor")) == hint


def _assert_avatar(item, border, content):
    assert item.property("_avatarBorderWidth") == 1
    assert _rgb(item.property("_avatarBorderColor")) == border
    assert _rgb(item.property("_avatarContentColor")) == content


def _assert_marquee(item):
    assert item.property("forceScroll") is True
    assert item.property("_needsScroll") is True
    assert item.property("pauseDuration") == 1000


def _assert_watermark(item, text_color):
    assert item.property("fontSize") == 14
    assert round(item.property("opacity_"), 2) == 0.3
    assert _rgb(item.property("textColor")) == text_color


def _list_item_qml():
    list_dir = (
        Path(__file__).resolve().parents[2]
        / "prismqml"
        / "PrismQML"
        / "controls"
        / "data"
        / "List"
    )
    list_dir_url = QUrl.fromLocalFile(str(list_dir)).toString()
    return f"""
import QtQuick
import PrismQML
import "{list_dir_url}" as ListInternal

Item {{
    property color revealGlowColor: item._revealGlowColor

    ListInternal.ListWidgetItem {{
        id: item
        itemIndex: 0
        itemData: "Alpha"
    }}
}}
""".encode()


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
            (22, 124, 128),
            (252, 254, 253),
            (199, 212, 211),
            (255, 255, 255),
            (86, 106, 109),
            (21, 35, 38),
        )

        keep.append(_build(engine, b"""
import PrismQML
CircularGauge {
    value: 42
    unit: "%"
}
"""))
        gauge = keep[-1][1]
        _assert_gauge(gauge, (225, 233, 231), (22, 124, 128), (122, 141, 144))

        keep.append(_build(engine, b"""
import PrismQML
IndicatorBar {
    active: false
    colorStyle: Enums.indicatorBar.style_gradient
}
"""))
        indicator = keep[-1][1]
        _assert_indicator(indicator, (22, 124, 128), (142, 164, 163))
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
        _assert_audio(audio, (221, 230, 228), (22, 124, 128))

        keep.append(_build(engine, b"""
import PrismQML
ImageWidget {
    width: 96
    height: 64
}
"""))
        image_widget = keep[-1][1]
        _assert_image_widget(image_widget, (230, 238, 237), (22, 124, 128))

        keep.append(_build(engine, b"""
import PrismQML
QRCode {
    content: ""
}
"""))
        qr_code = keep[-1][1]
        _assert_qr_code(qr_code, (199, 212, 211), (86, 106, 109))

        keep.append(_build(engine, b"""
import PrismQML
Avatar {
    text: "Prism"
}
"""))
        avatar = keep[-1][1]
        _assert_avatar(avatar, (142, 164, 163), (255, 255, 255))

        keep.append(_build(engine, b"""
import PrismQML
AvatarSelector {
    text: "Prism"
    enableCrop: false
    changeText: "Change"
}
"""))
        avatar_selector = keep[-1][1]
        _assert_avatar(avatar_selector, (142, 164, 163), (255, 255, 255))
        assert avatar_selector.property("enableCrop") is False
        assert avatar_selector.property("changeText") == "Change"

        keep.append(_build(engine, b"""
import PrismQML
Marquee {
    width: 120
    text: "Prism Design skin evidence"
    forceScroll: true
}
"""))
        marquee = keep[-1][1]
        _assert_marquee(marquee)

        keep.append(_build(engine, b"""
import PrismQML
Watermark {
    width: 240
    height: 120
    text: "PRISM"
}
"""))
        watermark = keep[-1][1]
        _assert_watermark(watermark, (122, 141, 144))

        keep.append(_build(engine, b"""
import PrismQML
DataWidgetCore {
    width: 240
    height: 140
    showHeader: true
}
"""))
        data_widget = keep[-1][1]
        assert _rgba(data_widget.property("_headerEdgeShadowColor")) == (16, 35, 38, 16)

        keep.append(_build(engine, _list_item_qml()))
        list_item = keep[-1][1]
        assert _rgba(list_item.property("revealGlowColor")) == (136, 220, 216, 31)

        setTheme(Theme.DARK)
        keep.append(_build(engine, b"""
import PrismQML
Badge {
    count: 7
    level: Enums.statusLevel.success
}
"""))
        dark_badge = keep[-1][1]
        assert _rgb(dark_badge.property("_contentColor")) == (6, 23, 24)

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
            (85, 214, 210),
            (25, 34, 36),
            (42, 57, 59),
            (6, 23, 24),
            (164, 181, 182),
            (238, 245, 243),
        )

        keep.append(_build(engine, b"""
import PrismQML
CircularGauge {
    value: 42
    unit: "%"
}
"""))
        dark_gauge = keep[-1][1]
        _assert_gauge(dark_gauge, (16, 23, 25), (85, 214, 210), (113, 134, 135))

        keep.append(_build(engine, b"""
import PrismQML
IndicatorBar {
    active: false
    colorStyle: Enums.indicatorBar.style_gradient
}
"""))
        dark_indicator = keep[-1][1]
        _assert_indicator(dark_indicator, (85, 214, 210), (73, 96, 99))

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
        _assert_audio(dark_audio, (34, 48, 51), (85, 214, 210))

        keep.append(_build(engine, b"""
import PrismQML
ImageWidget {
    width: 96
    height: 64
}
"""))
        dark_image_widget = keep[-1][1]
        _assert_image_widget(dark_image_widget, (29, 41, 43), (85, 214, 210))

        keep.append(_build(engine, b"""
import PrismQML
QRCode {
    content: ""
}
"""))
        dark_qr_code = keep[-1][1]
        _assert_qr_code(dark_qr_code, (42, 57, 59), (164, 181, 182))

        keep.append(_build(engine, b"""
import PrismQML
Avatar {
    text: "Prism"
}
"""))
        dark_avatar = keep[-1][1]
        _assert_avatar(dark_avatar, (73, 96, 99), (6, 23, 24))

        keep.append(_build(engine, b"""
import PrismQML
AvatarSelector {
    text: "Prism"
    enableCrop: false
    changeText: "Change"
}
"""))
        dark_avatar_selector = keep[-1][1]
        _assert_avatar(dark_avatar_selector, (73, 96, 99), (6, 23, 24))
        assert dark_avatar_selector.property("enableCrop") is False
        assert dark_avatar_selector.property("changeText") == "Change"

        keep.append(_build(engine, b"""
import PrismQML
Marquee {
    width: 120
    text: "Prism Design skin evidence"
    forceScroll: true
}
"""))
        dark_marquee = keep[-1][1]
        _assert_marquee(dark_marquee)

        keep.append(_build(engine, b"""
import PrismQML
Watermark {
    width: 240
    height: 120
    text: "PRISM"
}
"""))
        dark_watermark = keep[-1][1]
        _assert_watermark(dark_watermark, (113, 134, 135))

        keep.append(_build(engine, b"""
import PrismQML
DataWidgetCore {
    width: 240
    height: 140
    showHeader: true
}
"""))
        dark_data_widget = keep[-1][1]
        assert _rgba(dark_data_widget.property("_headerEdgeShadowColor")) == (0, 0, 0, 51)

        keep.append(_build(engine, _list_item_qml()))
        dark_list_item = keep[-1][1]
        assert _rgba(dark_list_item.property("revealGlowColor")) == (59, 220, 214, 41)
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
