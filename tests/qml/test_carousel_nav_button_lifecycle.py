# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Carousel navigation button lifecycle regressions. 轮播导航按钮生命周期回归。"""

from pathlib import Path

import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QPoint, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "data"
    / "Carousel"
    / "Carousel.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "carousel-nav-button-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: window

    readonly property int fastDuration: Enums.duration.fast
    readonly property var emptyModel: []
    readonly property var oneModel: [{ text: "A" }]
    readonly property var threeModel: [
        { text: "A" },
        { text: "B" },
        { text: "C" }
    ]

    width: 360
    height: 220
    visible: true
    color: Enums.backgroundColor

    Carousel {
        id: carousel
        objectName: "carousel"
        x: 20
        y: 20
        width: 320
        height: 180
        showIndicator: false
        model: window.threeModel
    }
}
"""


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _nav_buttons(carousel: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(carousel.childItems())
    while pending:
        item = pending.pop()
        if "CarouselNavButton" in item.metaObject().className():
            result.append(item)
        pending.extend(item.childItems())
    return sorted(result, key=lambda item: bool(item.property("isNext")))


def _point_for(item: QQuickItem) -> QPoint:
    center = item.mapToScene(item.boundingRect().center())
    return QPoint(round(center.x()), round(center.y()))


def _dispose_scene(engine, component, window) -> None:
    window.setVisible(False)
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_carousel_prepares_navigation_before_hover_and_first_click(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
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
    carousel = window.findChild(QQuickItem, "carousel")
    assert carousel is not None
    fast_duration = int(window.property("fastDuration"))
    QTest.qWait(fast_duration + 30)

    try:
        initial_buttons = _nav_buttons(carousel)
        assert len(initial_buttons) == 2
        assert all(not button.isVisible() for button in initial_buttons)

        window.requestActivate()
        QTest.qWait(30)
        QTest.mouseMove(window, QPoint(180, 110))
        QTest.qWait(fast_duration + 30)
        assert _nav_buttons(carousel) == initial_buttons
        assert all(button.isVisible() for button in initial_buttons)
        assert all(button.opacity() == 1 for button in initial_buttons)

        following = initial_buttons[1]
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            pos=_point_for(following),
        )
        assert carousel.property("currentIndex") == 1

        QTest.mouseMove(window, QPoint(1, 1))
        QTest.qWait(fast_duration + 30)
        carousel.setProperty("model", window.property("emptyModel"))
        QCoreApplication.processEvents()
        assert not any(button.isVisible() for button in _nav_buttons(carousel))
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()
        assert all(not shiboken6.isValid(button) for button in initial_buttons)

        carousel.setProperty("model", window.property("threeModel"))
        QCoreApplication.processEvents()
        prepared_buttons = _nav_buttons(carousel)
        assert len(prepared_buttons) == 2
        assert all(not button.isVisible() for button in prepared_buttons)

        QTest.mouseMove(window, QPoint(180, 110))
        QTest.qWait(fast_duration + 30)
        assert _nav_buttons(carousel) == prepared_buttons
        assert all(button.isVisible() for button in prepared_buttons)

        carousel.setProperty("model", window.property("oneModel"))
        QCoreApplication.processEvents()
        assert not any(button.isVisible() for button in _nav_buttons(carousel))

        carousel.setProperty("model", window.property("threeModel"))
        QCoreApplication.processEvents()
        revealing_buttons = _nav_buttons(carousel)
        assert len(revealing_buttons) == 2
        assert all(button.opacity() < 1 for button in revealing_buttons)
        QTest.qWait(fast_duration + 30)
        assert _nav_buttons(carousel) == revealing_buttons
        assert all(button.isVisible() for button in revealing_buttons)

        carousel.setProperty("showNavButtons", False)
        QCoreApplication.processEvents()
        assert not any(button.isVisible() for button in _nav_buttons(carousel))

        carousel.setProperty("showNavButtons", True)
        QCoreApplication.processEvents()
        QTest.qWait(fast_duration + 30)
        final_buttons = _nav_buttons(carousel)
        assert len(final_buttons) == 2
        assert all(button.isVisible() for button in final_buttons)
        assert all(shiboken6.isValid(button) for button in final_buttons)

        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_carousel_navigation_buttons_are_mode_gated_in_source():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    factory_source = (SOURCE_PATH.parent / "_internal" / "CarouselFactories.qml").read_text(
        encoding="utf-8"
    )
    assert "readonly property bool _hasNavButtons:" in source
    assert "CarouselNavButton {" not in source
    assert factory_source.count("CarouselNavButton {") == 1
    assert "carouselFactories.navButtonComponent.createObject(control" in source
    assert "previous._revealEnabled = true" in source
