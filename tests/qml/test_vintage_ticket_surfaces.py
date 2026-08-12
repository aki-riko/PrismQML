# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Vintage ticket core surface regressions. 复古票据核心表面回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPoint,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import Skin, getSkin, register_types, setSkin


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "vintage-ticket-surfaces.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    readonly property real cardOffset: elevatedCard.transform[0].y
    readonly property bool cardHovered: elevatedCard.hovered
    readonly property real ticketGradientFactor: Enums.button.gradientLighten
    readonly property real buttonBorderWidth: button.border.width
    readonly property color buttonBorderColor: button.border.color
    readonly property real cardBorderWidth: elevatedCard.border.width
    readonly property real inputBorderWidth: input.border.width

    function openPopup() { popup.openAtControl(button) }

    width: 720
    height: 420
    visible: true
    color: Enums.backgroundColor

    Button {
        id: button
        objectName: "button"
        x: 30
        y: 30
        width: 150
        height: 42
        text: "ADMIT ONE"
    }

    Card {
        id: elevatedCard
        objectName: "card"
        x: 30
        y: 100
        width: 240
        height: 120
        cardType: Enums.card.type_elevated
        clickEnabled: true
    }

    InputCore {
        id: input
        objectName: "input"
        x: 310
        y: 30
        width: 180
        height: 42
    }

    ComboBoxCore {
        id: combo
        objectName: "combo"
        x: 310
        y: 100
        width: 180
        model: ["A", "B"]
        currentIndex: 0
    }

    NavigationBarItem {
        id: navigationItem
        objectName: "navigationItem"
        x: 530
        y: 30
        width: 150
        height: 52
        text: "ARCHIVE"
        selected: true
    }

    NavigationBar {
        id: navigationBar
        objectName: "navigationBar"
        x: 530
        y: 100
        width: 150
        height: 200
        model: [
            {key: "archive", text: "ARCHIVE", icon: ""},
            {key: "tickets", text: "TICKETS", icon: ""}
        ]
        currentIndex: 0
        indicatorAnimationEnabled: false
    }

    PopupWindowCore {
        id: popup
        objectName: "popup"
        popupWidth: 180
        popupHeight: 120
        useInWindowPopup: true
        targetControl: button
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1200) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.childItems())
    return result


def _objects(root: QQuickItem, type_fragment: str) -> list[QQuickItem]:
    return [
        item
        for item in [root, *_descendants(root)]
        if type_fragment in item.metaObject().className()
    ]


def _sliding_indicators(root: QQuickItem) -> list[QQuickItem]:
    return [
        item
        for item in _objects(root, "SlidingIndicator")
        if "SlidingIndicatorAnimation" not in item.metaObject().className()
    ]


def _visibility_chain(item: QQuickItem) -> list[tuple[str, bool, float]]:
    chain = []
    current = item
    while current is not None:
        chain.append(
            (
                current.metaObject().className(),
                current.isVisible(),
                current.opacity(),
            )
        )
        current = current.parentItem()
    return chain


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
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    assert _wait_for(window.isExposed)
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
def ticket_scene(qapp):
    previous_skin = getSkin()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    setSkin(Skin.VINTAGE_TICKET)
    engine, component, window, warnings = _create_scene()
    try:
        yield window, warnings, windows_before
    finally:
        _dispose_scene(engine, component, window)
        setSkin(previous_skin)
        _pump()
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_ticket_core_surfaces_use_square_ink_geometry(ticket_scene):
    window, warnings, windows_before = ticket_scene
    button = window.findChild(QQuickItem, "button")
    card = window.findChild(QQuickItem, "card")
    input_control = window.findChild(QQuickItem, "input")
    combo = window.findChild(QQuickItem, "combo")
    navigation_item = window.findChild(QQuickItem, "navigationItem")
    navigation_bar = window.findChild(QQuickItem, "navigationBar")
    popup = window.findChild(QQuickItem, "popup")
    assert all((button, card, input_control, combo, navigation_item, navigation_bar, popup))

    assert button.property("radius") == 0
    assert window.property("buttonBorderWidth") == pytest.approx(1)
    assert window.property("buttonBorderColor") == QColor("#5a4637")
    assert card.property("borderRadius") == 0
    assert window.property("cardBorderWidth") == pytest.approx(1)
    assert input_control.property("radius") == 0
    assert window.property("inputBorderWidth") == pytest.approx(1)
    assert combo.property("radius") == 0
    assert navigation_item.property("_navItemRadius") == 0
    assert navigation_item.property("_navItemBorderWidth") == 1
    navigation_indicators = _sliding_indicators(navigation_bar)
    assert len(navigation_indicators) == 1
    assert not navigation_indicators[0].property("visible")
    assert popup.property("popupRadius") == 0
    assert popup.property("_popupBorderWidth") == 1
    assert window.property("ticketGradientFactor") == pytest.approx(1.0)
    assert warnings == []
    assert [item for item in QGuiApplication.topLevelWindows() if item.isVisible()] == [
        window
    ]


def test_navigation_repaints_when_switching_square_ticket_geometry(ticket_scene):
    window, warnings, _windows_before = ticket_scene
    navigation_bar = window.findChild(QQuickItem, "navigationBar")
    navigation_indicators = _sliding_indicators(navigation_bar)
    assert len(navigation_indicators) == 1

    setSkin(Skin.FLUENT)
    assert _wait_for(lambda: navigation_indicators[0].property("visible"))
    setSkin(Skin.VINTAGE_TICKET)
    assert _wait_for(lambda: not navigation_indicators[0].property("visible"))
    _pump()

    assert warnings == []


def test_ticket_surfaces_have_paper_without_elevation_or_neo_shadow(ticket_scene):
    window, warnings, _windows_before = ticket_scene
    ticket_papers = _objects(window.contentItem(), "TicketPaper")
    neo_shadows = _objects(window.contentItem(), "NeoShadow")
    rectangular_shadows = _objects(window.contentItem(), "RectangularShadow")
    popup_shadow = window.findChild(QQuickItem, "_popupShadow")
    popup_neo_shadow = window.findChild(QQuickItem, "_popupNeoShadow")
    popup_surface = window.findChild(QQuickItem, "_popupSurface")
    popup = window.findChild(QQuickItem, "popup")

    assert len(ticket_papers) >= 1
    assert all(item.property("visible") for item in ticket_papers)
    assert popup is not None
    assert popup_surface is not None
    assert len(_objects(popup_surface, "TicketPaper")) == 1
    assert QMetaObject.invokeMethod(window, "openPopup")
    assert _wait_for(
        lambda: popup.property("isOpen") and popup.property("_surfaceVisible")
    )
    assert _wait_for(
        lambda: len(_objects(window.contentItem(), "TicketPaper")) >= 2
    ), [
        _visibility_chain(item)
        for item in _objects(popup, "TicketPaper")
    ]
    assert all(not item.isVisible() for item in neo_shadows)
    assert rectangular_shadows
    assert all(not item.property("visible") for item in rectangular_shadows)
    assert popup_shadow is not None and not popup_shadow.property("visible")
    assert popup_neo_shadow is not None and not popup_neo_shadow.property("visible")
    assert warnings == []


def test_ticket_elevated_card_does_not_float_on_real_hover(ticket_scene):
    window, warnings, _windows_before = ticket_scene
    QTest.mouseMove(window, QPoint(120, 150))
    assert _wait_for(lambda: window.property("cardHovered"))
    _pump(250)
    assert window.property("cardOffset") == pytest.approx(0.0)
    assert warnings == []
