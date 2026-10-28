# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Filled status-level ink contrast contract. 填充状态等级的墨色对比度契约。

A filled button paints its label with `ContrastInk.onFill(fill, white, black)`, so any
light-theme semantic fill whose white contrast falls under 4.5 silently switches that
one level to black ink and it reads as a different visual family. attention and caution
used to sit at 3.65:1 and 3.26:1; this contract keeps every level above the threshold
so all seven share one ink.
填充按钮用 `ContrastInk.onFill(fill, 白, 黑)` 决定文字色，因此任何白字对比度低于 4.5
的浅色语义填充只会让那一级悄悄变成黑字，观感上就成了另一套视觉家族。attention 与
caution 原先只有 3.65:1 与 3.26:1；本契约要求每一级都过线，七级共用同一个墨色。
"""

import pytest
from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Theme, register_types, setTheme


#: WCAG 2.1 AA for normal-size text. 正文字号的 WCAG 2.1 AA 门槛。
MIN_CONTRAST = 4.5

SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    id: root

    readonly property var fills: {
        var out = []
        for (var level = 0; level <= 6; level++) {
            out.push({
                level: level,
                fill: Enums.statusLevel.getColorByLevel(level).toString()
            })
        }
        return out
    }

    readonly property color white: Enums.accentForeground
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _linearize(component: float) -> float:
    return (
        component / 12.92
        if component <= 0.03928
        else ((component + 0.055) / 1.055) ** 2.4
    )


def _relative_luminance(color: QColor) -> float:
    return (
        0.2126 * _linearize(color.redF())
        + 0.7152 * _linearize(color.greenF())
        + 0.0722 * _linearize(color.blueF())
    )


def _contrast_ratio(first: QColor, second: QColor) -> float:
    first_luminance = _relative_luminance(first)
    second_luminance = _relative_luminance(second)
    lighter = max(first_luminance, second_luminance)
    darker = min(first_luminance, second_luminance)
    return (lighter + 0.05) / (darker + 0.05)


def _variant(value):
    converter = getattr(value, "toVariant", None)
    return converter() if callable(converter) else value


def _load(qapp, theme):
    setTheme(theme)
    engine = QQmlApplicationEngine()
    engine.addImportPath("prismqml")
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, QUrl("status-level-filled-ink.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create()
    assert root is not None, [error.toString() for error in component.errors()]
    return engine, component, root


@pytest.mark.parametrize("theme", [Theme.LIGHT])
def test_light_filled_status_levels_share_the_white_ink(qapp, theme):
    """浅色主题七级填充都必须让白字达到 AA，否则其中几级会掉回黑字。"""
    engine, component, root = _load(qapp, theme)
    try:
        white = QColor(root.property("white"))
        assert white == QColor("#ffffff"), white.name()

        fills = _variant(root.property("fills"))
        assert len(fills) == 7, fills

        failing = []
        for row in fills:
            fill = QColor(row["fill"])
            ratio = _contrast_ratio(fill, white)
            if ratio < MIN_CONTRAST:
                failing.append((row["level"], fill.name(), round(ratio, 2)))

        assert not failing, (
            "这些状态等级的填充在白色墨色下低于 WCAG AA，会单独掉成黑字："
            f"{failing}"
        )
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump(40)


def test_caution_and_attention_stay_distinct_after_darkening(qapp):
    """压深以保证白字达标后，谨慎仍必须与警告可区分。"""
    engine, component, root = _load(qapp, Theme.LIGHT)
    try:
        fills = {row["level"]: QColor(row["fill"]) for row in _variant(root.property("fills"))}
        caution = fills[6]
        warning = fills[2]
        assert caution != warning, (caution.name(), warning.name())

        # 渠道距离太近会让"谨慎"和"警告"在色弱观察下混为一谈。
        distance = sum(
            (getattr(caution, channel)() - getattr(warning, channel)()) ** 2
            for channel in ("red", "green", "blue")
        ) ** 0.5
        assert distance >= 30, (caution.name(), warning.name(), round(distance, 1))
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump(40)
