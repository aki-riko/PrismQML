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
ANIMATIONS_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "utils"
    / "_internal"
    / "PopupAnimations.qml"
)
SURFACE_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "utils"
    / "_internal"
    / "PopupSurface.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "popup-window-animation-metrics.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property int showOpacityDuration: Enums.popupMetrics.showOpacityDuration
    readonly property int showRevealDuration: Enums.popupMetrics.showRevealDuration
    readonly property int hideOpacityDuration: Enums.popupMetrics.hideOpacityDuration
    readonly property int hideRevealDuration: Enums.popupMetrics.hideRevealDuration

    width: 320
    height: 240

    PopupWindowCore {
        id: popup
        objectName: "popup"
        popupWidth: 200
        popupHeight: 180

        Rectangle {
            objectName: "overflowProbe"
            x: -Enums.spacing.m
            y: -Enums.spacing.m
            width: parent.width + 2 * Enums.spacing.m
            height: parent.height + 2 * Enums.spacing.m
        }
    }

    PopupWindowCore {
        id: autoSizedPopup
        objectName: "autoSizedPopup"
        contentPadding: Enums.spacing.m
        implicitContentWidth: 240
        implicitContentHeight: 96

        Rectangle {
            objectName: "autoSizedContent"
            anchors.fill: parent
        }
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
        surface = popup.findChild(QQuickItem, "_popupSurface")
        assert surface is not None
        assert surface.property("opacity") == pytest.approx(0.0)
        expected = {
            "show_opacity": root.property("showOpacityDuration"),
            "show_reveal": root.property("showRevealDuration"),
            "hide_opacity": root.property("hideOpacityDuration"),
            "hide_reveal": root.property("hideRevealDuration"),
        }
        assert expected == {
            "show_opacity": 120,
            "show_reveal": 240,
            "hide_opacity": 100,
            "hide_reveal": 110,
        }

        animations = _number_animations(popup)
        targets = {
            "show_opacity": _find_animation(animations, "opacity", 0, 1),
            "show_reveal": _find_animation(animations, "_clipHeight", 0, 180),
            "hide_opacity": _find_animation(animations, "opacity", 1, 0),
            "hide_reveal": _find_animation(animations, "_clipHeight", 180, 0),
        }
        assert {
            name: animation.property("duration")
            for name, animation in targets.items()
        } == expected
        assert popup.property("isOpen") is False
        assert popup.property("isClosing") is False
        assert popup.findChildren(QWindow) == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_popup_window_content_clips_overflow_for_every_consumer(qapp):
    engine, component, root = _create_scene()
    try:
        popup = root.findChild(QQuickItem, "popup")
        assert popup is not None
        content = popup.findChild(QQuickItem, "_popupContent")
        overflow_probe = popup.findChild(QQuickItem, "overflowProbe")
        assert content is not None
        assert overflow_probe is not None
        assert overflow_probe.parentItem() is content
        assert overflow_probe.x() < 0
        assert overflow_probe.y() < 0
        assert overflow_probe.width() > content.width()
        assert overflow_probe.height() > content.height()
        assert popup.property("availableContentWidth") == 192
        assert popup.property("availableContentHeight") == 172
        assert (content.width(), content.height()) == pytest.approx((192, 172))
        assert content.clip()
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_popup_window_content_size_includes_padding_automatically(qapp):
    engine, component, root = _create_scene()
    try:
        popup = root.findChild(QQuickItem, "autoSizedPopup")
        content = popup.findChild(QQuickItem, "_popupContent") if popup else None
        assert popup is not None
        assert content is not None
        assert popup.property("popupWidth") == 256
        assert popup.property("popupHeight") == 112
        assert popup.property("availableContentWidth") == 240
        assert popup.property("availableContentHeight") == 96
        assert (content.width(), content.height()) == pytest.approx((240, 96))
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_popup_shadow_tracks_panel_geometry_not_animation_clip(qapp):
    engine, component, root = _create_scene()
    try:
        popup = root.findChild(QQuickItem, "popup")
        shadow = popup.findChild(QQuickItem, "_popupShadow") if popup else None
        neo_shadow = popup.findChild(QQuickItem, "_popupNeoShadow") if popup else None
        assert popup is not None
        assert shadow is not None
        assert neo_shadow is not None

        popup.setProperty("popupHeight", 84)
        popup.setProperty("_clipHeight", 308)
        _pump()

        assert (shadow.width(), shadow.height()) == pytest.approx((200, 84))
        assert (neo_shadow.width(), neo_shadow.height()) == pytest.approx((200, 84))
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_popup_surface_margin_contains_the_full_shadow_extent(qapp):
    engine, component, root = _create_scene()
    try:
        popup = root.findChild(QQuickItem, "popup")
        assert popup is not None
        panel_offset = float(popup.property("_panelOffset"))
        shadow_blur = float(popup.property("_popupShadowBlur"))
        shadow_offset = float(popup.property("_popupShadowOffset"))
        shadow = popup.findChild(QQuickItem, "_popupShadow")
        material = shadow.property("material") if shadow else None

        assert panel_offset >= shadow_blur + abs(shadow_offset)
        assert shadow is not None
        assert material is not None
        assert shadow.x() + material.x() >= -1e-6
        assert shadow.y() + material.y() >= -1e-6
        assert (
            shadow.x() + material.x() + material.width()
            <= popup.property("_outerWidth") + 1e-6
        )
        assert (
            shadow.y() + material.y() + material.height()
            <= popup.property("_outerHeight") + 1e-6
        )
        assert popup.property("_outerWidth") == pytest.approx(
            popup.property("popupWidth") + 2 * panel_offset
        )
        assert popup.property("_outerHeight") == pytest.approx(
            popup.property("popupHeight") + 2 * panel_offset
        )
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_popup_window_animation_source_uses_role_tokens():
    metrics_source = METRICS_SOURCE.read_text(encoding="utf-8")
    animation_source = ANIMATIONS_SOURCE.read_text(encoding="utf-8")
    metrics_block = metrics_source.split(
        "readonly property QtObject popup: QtObject {", 1
    )[1].split("// ==================== InfoBar", 1)[0]
    animation_block = animation_source

    for declaration in (
        "readonly property int showOpacityDuration: 120",
        "readonly property int showRevealDuration: 240",
        "readonly property int hideOpacityDuration: 100",
        "readonly property int hideRevealDuration: 110",
    ):
        assert declaration in metrics_block
    for binding in (
        "duration: Enums.popupMetrics.showOpacityDuration",
        "duration: Enums.popupMetrics.showRevealDuration",
        "duration: Enums.popupMetrics.hideOpacityDuration",
        "duration: Enums.popupMetrics.hideRevealDuration",
    ):
        assert binding in animation_block
    for legacy_name in ("fadeInDuration", "settleDuration", "hideDuration"):
        assert legacy_name not in metrics_block
    assert (
        re.search(r"duration\s*:\s*(?:120|240|1|100|110)\b", animation_block)
        is None
    )


def test_popup_reveal_mask_uses_the_full_popup_container():
    surface_source = SURFACE_SOURCE.read_text(encoding="utf-8")
    assert 'layer.effect: MultiEffect {' in surface_source
    assert 'maskSource: ShaderEffectSource {' in surface_source
    assert "width: popupPanel.width" in surface_source
    assert 'objectName: "_popupRevealMask"' in surface_source
    assert "sourceItem: Item {" in surface_source
    assert "hideSource: true" not in surface_source
    assert "height: popupPanel.height" in surface_source
    assert "clip: true" in surface_source
    assert "height: surface.clipHeight" in surface_source
    assert 'objectName: "_popupRevealCover"' not in surface_source
