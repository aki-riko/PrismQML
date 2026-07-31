# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Icon-only button padding regressions. 纯图标按钮内边距回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "button-icon-only-padding.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    id: root

    readonly property int iconOnlyPadding: Enums.spacing.xs
    readonly property int iconOnlyIconSize: Enums.iconSize.xxl
    readonly property int regularIconSize: Enums.iconSize.m
    readonly property int textContentPadding: Enums.spacing.m
    readonly property int buttonHeight: Enums.controlSize.buttonHeight
    readonly property int buttonMinWidth: Enums.controlSize.buttonMinWidth

    width: 320
    height: 120

    Button {
        id: iconOnlyButton
        objectName: "iconOnlyButton"
        icon: Enums.icon.checkmark
    }

    Button {
        id: explicitIconOnlyButton
        objectName: "explicitIconOnlyButton"
        x: 40
        icon: Enums.icon.image
        iconSize: Enums.iconSize.m
    }

    Button {
        id: textOnlyButton
        objectName: "textOnlyButton"
        y: 40
        text: "Send"
    }

    Button {
        id: iconTextButton
        objectName: "iconTextButton"
        x: 100
        y: 40
        icon: Enums.icon.checkmark
        text: "Send"
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump()
    assert warnings == []
    return engine, component, root, warnings


def _button(root, name):
    button = root.findChild(QObject, name)
    assert button is not None
    return button


def _descendants(root):
    result = []
    pending = list(root.children())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.children())
    return result


def _content_module(button):
    matches = [
        child
        for child in _descendants(button)
        if child.metaObject().indexOfProperty("_ringBorderColor") >= 0
        and child.metaObject().indexOfProperty("countdownRemaining") >= 0
    ]
    assert len(matches) == 1
    return matches[0]


def _icon_item(button):
    matches = [
        child
        for child in _descendants(button)
        if child.metaObject().className().startswith("Icon_QMLTYPE_")
        and child.metaObject().indexOfProperty("icon") >= 0
        and child.property("icon") == button.property("icon")
    ]
    assert len(matches) == 1
    return matches[0]


@pytest.fixture
def button_scene(qapp):
    engine, component, root, warnings = _create_scene()
    try:
        yield root, warnings
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def _assert_icon_only_extent(button, expected_extent):
    assert button.property("isToolButton")
    assert button.property("contentWidth") == pytest.approx(expected_extent)
    assert button.property("contentHeight") == pytest.approx(expected_extent)
    assert button.width() == pytest.approx(expected_extent)
    assert button.height() == pytest.approx(expected_extent)


def test_icon_only_button_keeps_extent_and_uses_larger_default_icon(button_scene):
    root, warnings = button_scene
    button = _button(root, "iconOnlyButton")
    expected_extent = root.property("buttonHeight")
    expected_icon_size = root.property("iconOnlyIconSize")

    _assert_icon_only_extent(button, expected_extent)
    assert button.property("iconSize") == expected_icon_size
    assert _icon_item(button).property("iconSize") == expected_icon_size
    assert (expected_extent - expected_icon_size) / 2 == root.property(
        "iconOnlyPadding"
    )
    assert warnings == []


def test_icon_only_button_respects_explicit_icon_size(button_scene):
    root, warnings = button_scene
    button = _button(root, "explicitIconOnlyButton")

    _assert_icon_only_extent(button, root.property("buttonHeight"))
    assert button.property("iconSize") == root.property("regularIconSize")
    assert _icon_item(button).property("iconSize") == root.property(
        "regularIconSize"
    )
    assert warnings == []


def test_text_content_keeps_existing_button_metrics(button_scene):
    root, warnings = button_scene
    for name in ("textOnlyButton", "iconTextButton"):
        button = _button(root, name)
        expected_width = max(
            root.property("buttonMinWidth"),
            _content_module(button).width() + root.property("textContentPadding") * 2,
        )
        assert not button.property("isToolButton")
        assert button.property("iconSize") == root.property("regularIconSize")
        assert button.property("contentWidth") == pytest.approx(expected_width)
        assert button.property("contentHeight") == pytest.approx(
            root.property("buttonHeight")
        )
        assert button.width() == pytest.approx(expected_width)
        assert button.height() == pytest.approx(root.property("buttonHeight"))
    assert warnings == []


def test_button_recomputes_extent_when_text_is_added_or_removed(button_scene):
    root, warnings = button_scene
    button = _button(root, "iconOnlyButton")
    button_extent = root.property("buttonHeight")

    assert button.property("iconSize") == root.property("iconOnlyIconSize")

    button.setProperty("text", "Send")
    _pump()
    expanded_width = max(
        root.property("buttonMinWidth"),
        _content_module(button).width() + root.property("textContentPadding") * 2,
    )
    assert not button.property("isToolButton")
    assert button.property("iconSize") == root.property("regularIconSize")
    assert button.property("contentWidth") == pytest.approx(expanded_width)
    assert button.property("contentHeight") == pytest.approx(
        root.property("buttonHeight")
    )

    button.setProperty("text", "")
    _pump()
    assert button.property("isToolButton")
    assert button.property("iconSize") == root.property("iconOnlyIconSize")
    assert button.property("contentWidth") == pytest.approx(button_extent)
    assert button.property("contentHeight") == pytest.approx(button_extent)
    assert button.width() == pytest.approx(button_extent)
    assert button.height() == pytest.approx(button_extent)
    assert warnings == []
