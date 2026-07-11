# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Accent foreground consumer regressions. 主色前景消费者回归。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, register_types, setSkin, setTheme


ROOT = Path(__file__).resolve().parents[2]
STEPPER_SOURCE = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "data" / "Step" / "Stepper.qml"
)
OFFLINE_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "feedback"
    / "State"
    / "OfflineState.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "accent-foreground-consumers.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    id: root

    readonly property color accentForeground: Enums.accentForeground
    readonly property color accentColor: Enums.accentColor
    readonly property var checkmarkIcon: Enums.icon.checkmark

    width: 720
    height: 240

    Stepper {
        objectName: "stepper"
        width: 500
        steps: [
            { text: "Done" },
            { text: "Current" },
            { text: "Pending" }
        ]
        currentStep: 1
    }

    OfflineState {
        objectName: "offlineState"
        x: 520
        width: 200
        height: 220
        retryText: "Retry Now"
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
    _pump(10)
    return engine, component, root


def _walk_visual_tree(root: QQuickItem):
    stack = [root]
    while stack:
        item = stack.pop()
        yield item
        stack.extend(reversed(item.childItems()))


def _find_unique(root: QQuickItem, predicate, label: str) -> QQuickItem:
    matches = [item for item in _walk_visual_tree(root) if predicate(item)]
    assert len(matches) == 1, (
        label,
        [item.metaObject().className() for item in matches],
    )
    return matches[0]


def _foreground_items(root: QQuickItem) -> tuple[QQuickItem, ...]:
    stepper = root.findChild(QQuickItem, "stepper")
    offline = root.findChild(QQuickItem, "offlineState")
    assert stepper is not None and offline is not None
    checkmark = _find_unique(
        stepper,
        lambda item: item.metaObject().indexOfProperty("icon") >= 0
        and item.property("icon") == root.property("checkmarkIcon")
        and item.isVisible(),
        "completed step icon",
    )
    current_number = _find_unique(
        stepper,
        lambda item: item.metaObject().indexOfProperty("text") >= 0
        and item.property("text") == "2"
        and item.isVisible(),
        "current step number",
    )
    retry_text = _find_unique(
        offline,
        lambda item: item.metaObject().indexOfProperty("text") >= 0
        and item.property("text") == "Retry Now",
        "offline retry text",
    )
    return checkmark, current_number, retry_text


def _argb(color: QColor) -> str:
    return color.name(QColor.NameFormat.HexArgb).lower()


def _wait_for_colors(
    items: tuple[QQuickItem, ...], expected: str, timeout_ms: int = 1000
) -> None:
    poll_ms = 10
    for _ in range(timeout_ms // poll_ms):
        actual = {_argb(item.property("color")) for item in items}
        if actual == {expected}:
            return
        _pump(poll_ms)
    assert {_argb(item.property("color")) for item in items} == {expected}


def test_accent_foreground_consumers_follow_theme_token(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.FLUENT)
    engine, component, root = _create_scene()
    try:
        items = _foreground_items(root)
        for theme, skin in (
            (Theme.LIGHT, Skin.FLUENT),
            (Theme.DARK, Skin.FLUENT),
            (Theme.LIGHT, Skin.NEOBRUTALISM),
            (Theme.DARK, Skin.NEOBRUTALISM),
        ):
            setTheme(theme)
            setSkin(skin)
            expected = _argb(root.property("accentForeground"))
            _wait_for_colors(items, expected)

        assert _argb(root.property("accentColor")) == "#fffb923c"
        assert _argb(root.property("accentForeground")) == "#ff1a1a1a"
    finally:
        setSkin(Skin.FLUENT)
        setTheme(Theme.LIGHT)
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_accent_foreground_sources_use_shared_token():
    stepper_source = STEPPER_SOURCE.read_text(encoding="utf-8")
    offline_source = OFFLINE_SOURCE.read_text(encoding="utf-8")

    check_icon_props = stepper_source.split("id: checkIcon", 1)[1].split(
        "// Fade in animation", 1
    )[0]
    number_text_props = stepper_source.split("id: numberText", 1)[1].split(
        "// Hover effect", 1
    )[0]
    retry_text_props = offline_source.split("id: retryTextItem", 1)[1].split(
        "MouseArea {", 1
    )[0]

    assert "color: Enums.accentForeground" in check_icon_props
    assert (
        "color: isActive ? Enums.accentForeground : Enums.secondaryForeground"
        in number_text_props
    )
    assert "color: Enums.accentForeground" in retry_text_props
    assert '"white"' not in check_icon_props + number_text_props + retry_text_props
