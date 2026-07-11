# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""PopupWindowCore animation metric regressions. 弹窗核心动画度量回归。"""

import re
from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QWindow
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
METRICS_SOURCE = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"
POPUP_SOURCE = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "utils" / "PopupWindowCore.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "popup-window-animation-metrics.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property int showOpacityDuration: Enums.popupMetrics.showOpacityDuration
    readonly property int showScaleDuration: Enums.popupMetrics.showScaleDuration
    readonly property int clipRevealDuration: Enums.popupMetrics.clipRevealDuration
    readonly property int hideOpacityDuration: Enums.popupMetrics.hideOpacityDuration
    readonly property int hideScaleDuration: Enums.popupMetrics.hideScaleDuration

    width: 320
    height: 240

    PopupWindowCore {
        id: popup
        objectName: "popup"
        popupWidth: 200
        popupHeight: 180
    }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump(20)
    return engine, component, root


def _number_animations(popup: QQuickItem) -> list[QObject]:
    return [
        obj
        for obj in popup.findChildren(QObject)
        if obj.metaObject().className() == "QQuickNumberAnimation"
    ]


def _find_animation(
    animations: list[QObject], property_name: str, start: float, end: float
) -> QObject:
    matches = [
        animation
        for animation in animations
        if animation.property("property") == property_name
        and animation.property("from") == pytest.approx(start)
        and animation.property("to") == pytest.approx(end)
    ]
    assert len(matches) == 1, [
        (
            animation.property("property"),
            animation.property("from"),
            animation.property("to"),
            animation.property("duration"),
        )
        for animation in matches
    ]
    return matches[0]


def test_popup_window_animation_metrics_preserve_runtime_values(qapp):
    engine, component, root = _create_scene()
    try:
        popup = root.findChild(QQuickItem, "popup")
        assert popup is not None
        expected = {
            "show_opacity": root.property("showOpacityDuration"),
            "show_scale": root.property("showScaleDuration"),
            "clip_reveal": root.property("clipRevealDuration"),
            "hide_opacity": root.property("hideOpacityDuration"),
            "hide_scale": root.property("hideScaleDuration"),
        }
        assert expected == {
            "show_opacity": 120,
            "show_scale": 240,
            "clip_reveal": 1,
            "hide_opacity": 100,
            "hide_scale": 110,
        }

        animations = _number_animations(popup)
        targets = {
            "show_opacity": _find_animation(animations, "opacity", 0, 1),
            "show_scale": _find_animation(animations, "_scale", 0.7, 1),
            "clip_reveal": _find_animation(animations, "_clipHeight", 0, 180),
            "hide_opacity": _find_animation(animations, "opacity", 0, 0),
            "hide_scale": _find_animation(animations, "_scale", 0, 0.85),
        }
        assert {
            name: animation.property("duration")
            for name, animation in targets.items()
        } == expected
        assert popup.property("isOpen") is False
        assert popup.property("isClosing") is False
        windows = popup.findChildren(QWindow)
        assert len(windows) == 1
        assert not windows[0].isVisible()
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_popup_window_animation_source_uses_role_tokens():
    metrics_source = METRICS_SOURCE.read_text(encoding="utf-8")
    popup_source = POPUP_SOURCE.read_text(encoding="utf-8")
    metrics_block = metrics_source.split(
        "readonly property QtObject popup: QtObject {", 1
    )[1].split("// ==================== InfoBar", 1)[0]
    animation_block = popup_source.split(
        "// ==================== Show Animation", 1
    )[1].split("Timer {", 1)[0]

    for declaration in (
        "readonly property int showOpacityDuration: 120",
        "readonly property int showScaleDuration: 240",
        "readonly property int clipRevealDuration: 1",
        "readonly property int hideOpacityDuration: 100",
        "readonly property int hideScaleDuration: 110",
    ):
        assert declaration in metrics_block
    for binding in (
        "duration: Enums.popupMetrics.showOpacityDuration",
        "duration: Enums.popupMetrics.showScaleDuration",
        "duration: Enums.popupMetrics.clipRevealDuration",
        "duration: Enums.popupMetrics.hideOpacityDuration",
        "duration: Enums.popupMetrics.hideScaleDuration",
    ):
        assert binding in animation_block
    for legacy_name in ("fadeInDuration", "settleDuration", "hideDuration"):
        assert legacy_name not in metrics_block
    assert (
        re.search(r"duration\s*:\s*(?:120|240|1|100|110)\b", animation_block)
        is None
    )
