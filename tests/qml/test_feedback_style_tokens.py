# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Feedback style token runtime regressions. 反馈组件样式令牌运行时回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlProperty

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
TOAST_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "feedback"
    / "Notification"
    / "Toast.qml"
)
SPLASH_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "feedback"
    / "SplashScreen"
    / "SplashScreen.qml"
)
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "feedback-style.qml"))
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    id: root

    readonly property int spacingM: Enums.spacing.m
    readonly property int spacingL: Enums.spacing.l
    readonly property int cardElevate: Enums.spacing.cardElevate
    readonly property real radiusLarge: Enums.radius.large
    readonly property real radiusTiny: Enums.radius.tiny
    readonly property int borderNormal: Enums.border.normal
    readonly property int spacingMicro: Enums.spacing.micro
    readonly property int iconXl: Enums.iconSize.xl

    width: 640
    height: 480

    Toast {
        objectName: "toast"
        desktopMode: true
        duration: 0
        closable: false
        visible: true
    }

    SplashScreen {
        objectName: "splash"
        enableShadow: false
        showTitleBar: false
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
    _pump(1)
    return engine, component, root


def _walk_visual_tree(root: QQuickItem):
    stack = [root]
    while stack:
        item = stack.pop()
        yield item
        stack.extend(reversed(item.childItems()))


def _read(item: QQuickItem, name: str):
    prop = QQmlProperty(item, name)
    assert prop.isValid(), (item.metaObject().className(), name)
    return prop.read()


def _find_unique(items, predicate, label: str) -> QQuickItem:
    matches = [item for item in items if predicate(item)]
    assert len(matches) == 1, (
        label,
        [
            (
                item.metaObject().className(),
                item.x(),
                item.y(),
                item.width(),
                item.height(),
            )
            for item in matches
        ],
    )
    return matches[0]


def _toast_targets(
    toast: QQuickItem, spacing_l: int, radius_large: float
) -> tuple[QQuickItem, QQuickItem]:
    color_bar = _find_unique(
        list(_walk_visual_tree(toast)),
        lambda item: item.metaObject().className() == "QQuickRectangle"
        and item.height() == pytest.approx(spacing_l)
        and item.property("radius") == pytest.approx(radius_large),
        "toast color bar",
    )
    container = color_bar.parentItem()
    assert isinstance(container, QQuickItem)
    return container, color_bar


def _splash_targets(
    splash: QQuickItem, icon_xl: int, radius_tiny: float
) -> tuple[QQuickItem, QQuickItem]:
    items = list(_walk_visual_tree(splash))
    indicator = _find_unique(
        items,
        lambda item: item.metaObject().className() == "QQuickRectangle"
        and item.width() == pytest.approx(6)
        and item.height() == pytest.approx(6)
        and item.property("radius") == pytest.approx(radius_tiny),
        "splash arc indicator",
    )
    arc_layer = indicator.parentItem()
    progress_container = arc_layer.parentItem() if arc_layer is not None else None
    assert isinstance(progress_container, QQuickItem)
    progress_ring = _find_unique(
        progress_container.childItems(),
        lambda item: item is not arc_layer
        and item.width() == pytest.approx(icon_xl)
        and item.height() == pytest.approx(icon_xl)
        and item.property("radius") == pytest.approx(icon_xl / 2)
        and item.opacity() == pytest.approx(0.3),
        "splash progress ring",
    )
    return progress_ring, indicator


def _style_metrics(root: QQuickItem) -> dict[str, float]:
    metrics = {
        "spacing_m": root.property("spacingM"),
        "spacing_l": root.property("spacingL"),
        "card_elevate": root.property("cardElevate"),
        "radius_large": root.property("radiusLarge"),
        "radius_tiny": root.property("radiusTiny"),
        "border_normal": root.property("borderNormal"),
        "spacing_micro": root.property("spacingMicro"),
        "icon_xl": root.property("iconXl"),
    }
    assert tuple(metrics.values()) == (8, 12, 3, 8, 2, 2, 1, 20)
    return metrics


def _assert_toast_geometry(toast: QQuickItem, metrics: dict[str, float]) -> None:
    container, color_bar = _toast_targets(
        toast, metrics["spacing_l"], metrics["radius_large"]
    )
    expected_top = metrics["spacing_m"] + metrics["card_elevate"]
    assert _read(container, "anchors.topMargin") == expected_top
    assert container.x() == pytest.approx(metrics["spacing_m"])
    assert container.y() == pytest.approx(expected_top)
    assert _read(color_bar, "anchors.topMargin") == -metrics["card_elevate"]
    assert color_bar.y() == pytest.approx(-metrics["card_elevate"])
    assert container.y() + color_bar.y() == pytest.approx(metrics["spacing_m"])


def _assert_splash_geometry(splash: QQuickItem, metrics: dict[str, float]) -> None:
    progress_ring, indicator = _splash_targets(
        splash, metrics["icon_xl"], metrics["radius_tiny"]
    )
    assert _read(progress_ring, "border.width") == metrics["border_normal"]
    assert _read(indicator, "anchors.topMargin") == -metrics["spacing_micro"]
    assert indicator.y() == pytest.approx(-metrics["spacing_micro"])


def test_feedback_metrics_preserve_runtime_geometry(qapp):
    engine, component, root = _create_scene()
    try:
        metrics = _style_metrics(root)
        toast = root.findChild(QQuickItem, "toast")
        splash = root.findChild(QQuickItem, "splash")
        assert toast is not None and splash is not None
        _assert_toast_geometry(toast, metrics)
        _assert_splash_geometry(splash, metrics)
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_feedback_sources_use_shared_style_tokens():
    toast_source = TOAST_SOURCE.read_text(encoding="utf-8")
    splash_source = SPLASH_SOURCE.read_text(encoding="utf-8")

    assert (
        "anchors.topMargin: Enums.spacing.m + Enums.spacing.cardElevate"
        in toast_source
    )
    assert "anchors.topMargin: -Enums.spacing.cardElevate" in toast_source
    assert "Enums.spacing.m + 3" not in toast_source
    assert "anchors.topMargin: -3" not in toast_source

    assert "border.width: Enums.border.normal" in splash_source
    assert "anchors.topMargin: -Enums.spacing.micro" in splash_source
    assert "border.width: 2" not in splash_source
    assert "anchors.topMargin: -1" not in splash_source
