# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Status-level color accessibility regression tests."""

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, register_types, setSkin, setTheme


def _rgb(color):
    return color.red(), color.green(), color.blue()


def _linear_channel(channel):
    value = channel / 255
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def _luminance(color):
    red, green, blue = (_linear_channel(channel) for channel in _rgb(color))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _contrast_ratio(foreground, background):
    lighter, darker = sorted((_luminance(foreground), _luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def _build_status_probe(engine):
    component = QQmlComponent(engine)
    component.setData(
        b"""
import QtQuick
import PrismQML
QtObject {
    property color infoColor: Enums.statusLevel.getColor("info")
    property color warningColor: Enums.statusLevel.getColor("warning")
    property color infoBackground: Enums.statusLevel.getBgColor("info")
    property color warningBackground: Enums.statusLevel.getBgColor("warning")
}
""",
        QUrl("inline"),
    )
    assert not component.isError(), [error.toString() for error in component.errors()]
    item = component.create(engine.rootContext())
    assert item is not None, [error.toString() for error in component.errors()]
    return component, item


@pytest.mark.parametrize(
    ("theme", "expected_info", "expected_warning", "minimum_luminance_gap"),
    [
        (Theme.LIGHT, (0, 95, 184), (122, 62, 0), 0.035),
        (Theme.DARK, (96, 205, 255), (207, 121, 0), 0.20),
    ],
)
def test_info_and_warning_colors_remain_accessibly_distinct(
    qapp, theme, expected_info, expected_warning, minimum_luminance_gap
):
    setSkin(Skin.FLUENT)
    setTheme(theme)
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, item = _build_status_probe(engine)

    try:
        info = item.property("infoColor")
        warning = item.property("warningColor")
        assert _rgb(info) == expected_info
        assert _rgb(warning) == expected_warning
        assert _contrast_ratio(info, item.property("infoBackground")) >= 4.5
        assert _contrast_ratio(warning, item.property("warningBackground")) >= 4.5
        assert _luminance(info) - _luminance(warning) >= minimum_luminance_gap
    finally:
        item.deleteLater()
        del component
        setTheme(Theme.LIGHT)
        setSkin(Skin.FLUENT)
