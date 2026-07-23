# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design auxiliary data and media skin tests."""

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl
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
    assert item.property("_waveformRadius") == 14
    assert item.property("_waveformInnerRadius") == 10
    assert _rgb(item.property("_waveformBorderColor")) == border
    assert _rgb(item.property("_progressOverlayColor")) == overlay
    assert _alpha(item.property("_progressOverlayColor")) == 26


def _assert_image_widget(item, placeholder, icon):
    assert item.property("radius") == 10
    assert _rgb(item.property("_placeholderColor")) == placeholder
    assert _rgb(item.property("_placeholderIconColor")) == icon


def _assert_qr_code(item, border, hint):
    assert item.property("_qrPlaceholderRadius") == 10
    assert _rgb(item.property("_qrBorderColor")) == border
    assert _rgb(item.property("_qrHintColor")) == hint


def _assert_avatar(item, border, content):
    assert item.property("_avatarBorderWidth") == 1
    assert _rgb(item.property("_avatarBorderColor")) == border
    assert _rgb(item.property("_avatarContentColor")) == content


def _assert_marquee(item):
    content = item.findChild(QObject, "marqueeContent")
    text = item.findChild(QObject, "marqueeText")
    text_copy = item.findChild(QObject, "marqueeTextCopy")
    source = (
        Path(__file__).resolve().parents[2]
        / "prismqml"
        / "PrismQML"
        / "controls"
        / "data"
        / "Marquee.qml"
    ).read_text(encoding="utf-8")

    assert content is not None
    assert text is not None
    assert text_copy is not None
    assert item.property("forceScroll") is True
    assert item.property("_needsScroll") is True
    assert item.property("scrollGap") == item.property("expectedScrollGap")
    assert item.property("_scrollDistance") == pytest.approx(
        text.property("implicitWidth") + item.property("scrollGap")
    )
    assert text_copy.property("x") == pytest.approx(item.property("_scrollDistance"))
    assert item.property("pauseDuration") == 1000
    assert "ScriptAction" not in source
    assert "target: marqueeContent" in source


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
            (11, 127, 137),
            (252, 254, 255),
            (185, 204, 209),
            (255, 255, 255),
            (82, 105, 112),
            (18, 34, 38),
        )

        keep.append(_build(engine, b"""
import PrismQML
CircularGauge {
    value: 42
    unit: "%"
}
"""))
        gauge = keep[-1][1]
        _assert_gauge(gauge, (221, 233, 237), (11, 127, 137), (118, 138, 145))

        keep.append(_build(engine, b"""
import PrismQML
IndicatorBar {
    active: false
    colorStyle: Enums.indicatorBar.style_gradient
}
"""))
        indicator = keep[-1][1]
        _assert_indicator(indicator, (11, 127, 137), (120, 173, 184))
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
        _assert_audio(audio, (220, 233, 237), (11, 127, 137))

        keep.append(_build(engine, b"""
import PrismQML
ImageWidget {
    width: 96
    height: 64
}
"""))
        image_widget = keep[-1][1]
        _assert_image_widget(image_widget, (234, 244, 247), (11, 127, 137))

        keep.append(_build(engine, b"""
import PrismQML
QRCode {
    content: ""
}
"""))
        qr_code = keep[-1][1]
        _assert_qr_code(qr_code, (185, 204, 209), (82, 105, 112))

        keep.append(_build(engine, b"""
import PrismQML
Avatar {
    text: "Prism"
}
"""))
        avatar = keep[-1][1]
        _assert_avatar(avatar, (120, 173, 184), (255, 255, 255))

        keep.append(_build(engine, b"""
import PrismQML
AvatarSelector {
    text: "Prism"
    enableCrop: false
    changeText: "Change"
}
"""))
        avatar_selector = keep[-1][1]
        _assert_avatar(avatar_selector, (120, 173, 184), (255, 255, 255))
        assert avatar_selector.property("enableCrop") is False
        assert avatar_selector.property("changeText") == "Change"

        keep.append(_build(engine, b"""
import PrismQML
Marquee {
    width: 120
    property int expectedScrollGap: Enums.spacing.l
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
        _assert_watermark(watermark, (118, 138, 145))
        watermark.setProperty("gapX", 0)
        watermark.setProperty("gapY", 0)
        assert watermark.property("_safeGapX") == 1
        assert watermark.property("_safeGapY") == 1

        keep.append(_build(engine, b"""
import PrismQML
DataWidgetCore {
    width: 240
    height: 140
    showHeader: true
        }
"""))
        data_widget = keep[-1][1]
        assert _rgba(data_widget.property("_headerEdgeShadowColor")) == (112, 231, 242, 34)

        keep.append(_build(engine, _list_item_qml()))
        list_item = keep[-1][1]
        assert _rgba(list_item.property("revealGlowColor")) == (112, 231, 242, 31)

        setTheme(Theme.DARK)
        keep.append(_build(engine, b"""
import PrismQML
Badge {
    count: 7
    level: Enums.statusLevel.success
}
"""))
        dark_badge = keep[-1][1]
        assert _rgb(dark_badge.property("_contentColor")) == (4, 23, 25)

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
            (109, 235, 242),
            (26, 37, 41),
            (50, 72, 79),
            (4, 23, 25),
            (168, 186, 191),
            (238, 247, 248),
        )

        keep.append(_build(engine, b"""
import PrismQML
CircularGauge {
    value: 42
    unit: "%"
}
"""))
        dark_gauge = keep[-1][1]
        _assert_gauge(dark_gauge, (12, 21, 24), (109, 235, 242), (115, 138, 145))

        keep.append(_build(engine, b"""
import PrismQML
IndicatorBar {
    active: false
    colorStyle: Enums.indicatorBar.style_gradient
}
"""))
        dark_indicator = keep[-1][1]
        _assert_indicator(dark_indicator, (109, 235, 242), (106, 169, 181))

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
        _assert_audio(dark_audio, (38, 58, 65), (109, 235, 242))

        keep.append(_build(engine, b"""
import PrismQML
ImageWidget {
    width: 96
    height: 64
}
"""))
        dark_image_widget = keep[-1][1]
        _assert_image_widget(dark_image_widget, (33, 49, 54), (109, 235, 242))

        keep.append(_build(engine, b"""
import PrismQML
QRCode {
    content: ""
}
"""))
        dark_qr_code = keep[-1][1]
        _assert_qr_code(dark_qr_code, (50, 72, 79), (168, 186, 191))

        keep.append(_build(engine, b"""
import PrismQML
Avatar {
    text: "Prism"
}
"""))
        dark_avatar = keep[-1][1]
        _assert_avatar(dark_avatar, (106, 169, 181), (4, 23, 25))

        keep.append(_build(engine, b"""
import PrismQML
AvatarSelector {
    text: "Prism"
    enableCrop: false
    changeText: "Change"
}
"""))
        dark_avatar_selector = keep[-1][1]
        _assert_avatar(dark_avatar_selector, (106, 169, 181), (4, 23, 25))
        assert dark_avatar_selector.property("enableCrop") is False
        assert dark_avatar_selector.property("changeText") == "Change"

        keep.append(_build(engine, b"""
import PrismQML
Marquee {
    width: 120
    property int expectedScrollGap: Enums.spacing.l
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
        _assert_watermark(dark_watermark, (115, 138, 145))

        keep.append(_build(engine, b"""
import PrismQML
DataWidgetCore {
    width: 240
    height: 140
    showHeader: true
        }
"""))
        dark_data_widget = keep[-1][1]
        assert _rgba(dark_data_widget.property("_headerEdgeShadowColor")) == (122, 242, 255, 51)

        keep.append(_build(engine, _list_item_qml()))
        dark_list_item = keep[-1][1]
        assert _rgba(dark_list_item.property("revealGlowColor")) == (122, 242, 255, 41)
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
