# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Hyperlink button navigation and visited-state runtime contracts.

超链接按钮导航与已访问态运行时合同。
"""

from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "hyperlink-button-navigate.qml")
)

HYPERLINK_URL = "prismtest://w7/hyperlink"
PROGRAMMATIC_URL = "prismtest://w7/programmatic"

SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"
    width: 420
    height: 240
    visible: true

    property var openedUrls: []
    property int navigationRequests: 0
    property string lastRequestedUrl: ""

    readonly property color visitedToken: Enums.isDark
        ? Enums.button.hyperlinkVisitedDark : Enums.button.hyperlinkVisitedLight
    readonly property color accentToken: Enums.accentColor

    function recordUrl(url) {
        openedUrls = openedUrls.concat([url])
    }

    Button {
        id: hyperlinkButton
        objectName: "hyperlinkButton"
        x: 20
        y: 20
        width: 200
        height: 36
        text: "Open documentation"
        style: Enums.button.style_hyperlink
        navigateUri: "prismtest://w7/hyperlink"
        urlOpener: function(url) { root.recordUrl(url) }
        onNavigationRequested: (url) => {
            root.navigationRequests += 1
            root.lastRequestedUrl = url
        }
    }

    Button {
        id: plainHyperlink
        objectName: "plainHyperlink"
        x: 20
        y: 76
        width: 200
        height: 36
        text: "Plain hyperlink"
        style: Enums.button.style_hyperlink
        urlOpener: function(url) { root.recordUrl("plain:" + url) }
    }

    Button {
        id: programmaticButton
        objectName: "programmaticButton"
        x: 20
        y: 132
        width: 200
        height: 36
        text: "Programmatic"
        style: Enums.button.style_hyperlink
        navigateUri: "prismtest://w7/programmatic"
        urlOpener: function(url) { root.recordUrl(url) }
    }

    Button {
        id: defaultButton
        objectName: "defaultButton"
        x: 20
        y: 188
        width: 200
        height: 36
        text: "Default"
        style: Enums.button.style_hyperlink
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
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
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    _pump(60)
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(1)


def _button(window, name) -> QQuickItem:
    item = window.findChild(QQuickItem, name)
    assert item is not None, name
    return item


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _opened_urls(window):
    return list(_variant(window.property("openedUrls")))


def _click(window: QQuickWindow, item: QQuickItem) -> None:
    centre = item.mapToItem(
        window.contentItem(),
        QPointF(item.width() / 2.0, item.height() / 2.0),
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(centre.x()), round(centre.y())),
    )
    _pump(60)


def _move_away(window: QQuickWindow) -> None:
    """Park the pointer off the button so resting colors can be asserted.

    把指针移出按钮，以便断言静息色。
    """
    QTest.mouseMove(window, QPoint(window.width() - 2, window.height() - 2))
    _pump(80)


def _text_color(item: QQuickItem):
    return item.property("_styleTextColor")


def test_hyperlink_button_defaults_keep_plain_button_behavior(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        default_button = _button(window, "defaultButton")
        assert default_button.property("navigateUri") == ""
        assert default_button.property("navigateOnClick") is True
        assert default_button.property("urlOpener") is None
        assert default_button.property("visited") is False
        assert default_button.property("_styleTextColor") == window.property(
            "accentToken"
        )

        _click(window, default_button)
        _move_away(window)
        assert _opened_urls(window) == []
        assert default_button.property("visited") is False
        assert default_button.property("_styleTextColor") == window.property(
            "accentToken"
        )
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_hyperlink_click_opens_uri_and_switches_to_visited_color(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        button = _button(window, "hyperlinkButton")
        accent_token = window.property("accentToken")
        visited_token = window.property("visitedToken")
        assert visited_token != accent_token
        assert button.property("_styleTextColor") == accent_token

        _click(window, button)
        _move_away(window)

        assert _opened_urls(window) == [HYPERLINK_URL]
        assert window.property("navigationRequests") == 1
        assert window.property("lastRequestedUrl") == HYPERLINK_URL
        assert button.property("visited") is True
        assert _text_color(button) == visited_token
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_hyperlink_without_uri_keeps_accent_color_and_never_navigates(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        button = _button(window, "plainHyperlink")
        accent_token = window.property("accentToken")

        _click(window, button)
        _move_away(window)

        assert _opened_urls(window) == []
        assert button.property("visited") is False
        assert _text_color(button) == accent_token
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_programmatic_click_uses_the_same_navigation_path(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        button = _button(window, "programmaticButton")
        assert QMetaObject.invokeMethod(button, "click")
        _pump(30)

        assert _opened_urls(window) == [PROGRAMMATIC_URL]
        assert button.property("visited") is True
        assert _text_color(button) == window.property("visitedToken")
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_visited_hyperlink_keeps_hover_derivation(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        button = _button(window, "hyperlinkButton")
        accent_token = window.property("accentToken")
        visited_token = window.property("visitedToken")

        button.setProperty("visited", True)
        _pump(30)
        assert _text_color(button) == visited_token

        button.setProperty("pseudoHovered", True)
        _pump(30)
        hovered_color = _text_color(button)
        assert hovered_color != visited_token
        assert hovered_color != accent_token

        button.setProperty("pseudoHovered", False)
        _pump(30)
        assert _text_color(button) == visited_token
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_url_opener_override_suppresses_external_launch(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        button = _button(window, "hyperlinkButton")
        assert button.setProperty("navigateOnClick", False)
        _click(window, button)

        assert _opened_urls(window) == []
        assert window.property("navigationRequests") == 1
        assert button.property("visited") is True
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
