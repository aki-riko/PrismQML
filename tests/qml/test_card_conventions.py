# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Card geometry and interaction contracts. Card 几何与交互合同。"""

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPoint,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "card-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property int cardMinimumHeight: Enums.controlSize.cardHeight
    readonly property real fixedHeight: fixedCard.height
    readonly property real tallHeight: tallCard.height
    readonly property real shortHeight: shortCard.height
    readonly property real headerHeight: headerCard.height
    readonly property real headerContentHeight: headerContent.height
    readonly property real elevatedOffset: elevatedCard.transform[0].y
    readonly property bool elevatedHovered: elevatedCard.hovered
    readonly property bool elevatedPressed: elevatedCard.pressed
    readonly property real cardElevate: Enums.spacing.cardElevate

    width: 680
    height: 560
    visible: false

    Card {
        id: fixedCard
        objectName: "fixedCard"
        x: 20
        y: 20
        width: 220
        height: 80
        clickEnabled: false

        Rectangle { anchors.fill: parent }
    }

    Card {
        id: tallCard
        objectName: "tallCard"
        x: 260
        y: 20
        width: 220
        autoHeight: true

        Column {
            width: parent.width
            spacing: 6
            Repeater { model: 6; Rectangle { width: 100; height: 16 } }
        }
    }

    Card {
        id: shortCard
        objectName: "shortCard"
        x: 20
        y: 140
        width: 220
        autoHeight: true
        cardType: Enums.card.type_hover

        Rectangle { width: 100; height: 16 }
    }

    Card {
        id: headerCard
        objectName: "headerCard"
        x: 260
        y: 140
        width: 240
        cardType: Enums.card.type_header
        title: "Header title"

        Rectangle {
            id: headerContent
            objectName: "headerContent"
            width: parent.width
            height: 40
        }
    }

    Card {
        id: elevatedCard
        objectName: "elevatedCard"
        x: 20
        y: 320
        width: 220
        height: 90
        cardType: Enums.card.type_elevated
        clickEnabled: true
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is accepted for accepted in allowed)
    ]


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
    assert isinstance(window, QQuickWindow)
    _pump()
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture
def card_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene()
    try:
        yield window, warnings, windows_before
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_card_fixed_auto_and_header_heights(card_scene):
    window, warnings, windows_before = card_scene
    minimum_height = window.property("cardMinimumHeight")
    assert window.property("fixedHeight") == pytest.approx(80)
    assert window.property("shortHeight") == pytest.approx(minimum_height)
    assert window.property("tallHeight") > minimum_height
    assert window.property("tallHeight") > window.property("shortHeight")
    assert window.property("headerHeight") > window.property("headerContentHeight")
    header = window.findChild(QQuickItem, "headerCard")
    labels = [
        item
        for item in header.findChildren(QQuickItem)
        if item.property("text") == "Header title"
    ]
    assert len(labels) == 1
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_card_real_hover_press_and_click(card_scene):
    window, warnings, windows_before = card_scene
    elevated = window.findChild(QQuickItem, "elevatedCard")
    clicks = []
    elevated.clicked.connect(lambda: clicks.append(True))
    window.show()
    _pump()

    QTest.mouseMove(window, QPoint(100, 360))
    assert _wait_for(lambda: window.property("elevatedHovered"))
    assert _wait_for(
        lambda: window.property("elevatedOffset")
        == pytest.approx(-window.property("cardElevate"))
    )

    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=QPoint(100, 360))
    assert window.property("elevatedPressed")
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=QPoint(100, 360))
    assert _wait_for(lambda: clicks == [True])
    assert not window.property("elevatedPressed")

    window.hide()
    _pump()
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []
