# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Vintage ticket data and input regressions. 复古票据数据与输入回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlProperty
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import Skin, getSkin, register_types, setSkin


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "vintage-ticket-remaining-controls.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    readonly property real avatarRadius: avatar.radius
    readonly property real avatarBorderWidth: avatar.border.width
    readonly property real badgeRadius: badge.radius
    readonly property real badgeBorderWidth: badge.border.width
    readonly property real tagRadius: tag._tagRadius
    readonly property real tagBorderWidth: tag._tagBorderWidth
    readonly property real carouselRadius: carousel._effectiveBorderRadius
    readonly property real dataRadius: dataWidget._effectiveBorderRadius
    readonly property real treeRadius: tree._effectiveBorderRadius
    readonly property real tabRadius: tabs._selectedTabRadius
    readonly property real tabBorderWidth: tabs._selectedTabBorderWidth
    readonly property real chipRadius: chip._chipRadius
    readonly property real chipBorderWidth: chip._chipBorderWidth
    readonly property real pinRadius: pin._cellRadius
    readonly property real pinBorderWidth: pin._cellBorderWidth
    readonly property real sliderTrackRadius: slider._trackRadius
    readonly property real sliderHandleBorderWidth: slider._handleBorderWidth
    readonly property real beforeAfterRadius: beforeAfter._effectiveRadius

    width: 1100
    height: 760
    visible: true
    color: Enums.backgroundColor

    DataWidgetCore {
        id: dataWidget
        objectName: "ticketDataWidget"
        x: 20
        y: 20
        width: 300
        height: 190
    }

    TreeWidget {
        id: tree
        objectName: "ticketTree"
        x: 340
        y: 20
        width: 300
        height: 190
        headerLabels: ["PASSENGER"]
        model: []
    }

    TabWidget {
        id: tabs
        objectName: "ticketTabs"
        x: 660
        y: 20
        width: 400
        height: 100
        tabs: []
    }

    Carousel {
        id: carousel
        objectName: "ticketCarousel"
        x: 660
        y: 130
        width: 400
        height: 80
        borderRadius: Enums.radius.large
        shadowLevel: Enums.shadow.level4
        showIndicator: false
        showNavButtons: false
    }

    Chip {
        id: chip
        objectName: "ticketChip"
        x: 20
        y: 240
        text: "PLATFORM 04"
        checked: true
    }

    PinInput {
        id: pin
        objectName: "ticketPin"
        x: 20
        y: 300
        value: "42"
    }

    Slider {
        id: slider
        objectName: "ticketSlider"
        x: 20
        y: 380
        width: 300
        value: 62
    }

    BeforeAfterSlider {
        id: beforeAfter
        objectName: "ticketBeforeAfter"
        x: 340
        y: 240
        width: 300
        height: 180
    }

    Avatar {
        id: avatar
        objectName: "ticketAvatar"
        x: 680
        y: 250
        size: 44
        text: "A"
    }

    Badge {
        id: badge
        objectName: "ticketBadge"
        x: 750
        y: 260
        count: 4
    }

    Tag {
        id: tag
        objectName: "ticketTag"
        x: 820
        y: 250
        text: "VALID"
        showBorder: false
    }

    CheckBox {
        id: checkBox
        objectName: "ticketCheckBox"
        x: 680
        y: 330
        text: "Checked baggage"
        checked: true
    }

    RadioButton {
        id: radio
        objectName: "ticketRadio"
        x: 680
        y: 390
        text: "One way"
        checked: true
    }

    ToggleSwitch {
        id: toggleSwitch
        objectName: "ticketSwitch"
        x: 680
        y: 450
        text: "Boarding"
        checked: true
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
    _pump(80)
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


def _objects(root: QObject, type_fragment: str) -> list[QObject]:
    return [
        child
        for child in root.findChildren(QObject)
        if type_fragment in child.metaObject().className()
    ]


def _single(root: QObject, type_fragment: str) -> QQuickItem:
    matches = _objects(root, type_fragment)
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    assert isinstance(matches[0], QQuickItem)
    return matches[0]


@pytest.fixture
def ticket_controls(qapp):
    previous_skin = getSkin()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    setSkin(Skin.VINTAGE_TICKET)
    engine, component, window, warnings = _create_scene()
    try:
        yield window, warnings
    finally:
        _dispose_scene(engine, component, window)
        setSkin(previous_skin)
        _pump()
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_ticket_remaining_surfaces_use_square_ink_geometry(ticket_controls):
    window, warnings = ticket_controls
    for property_name in (
        "tagRadius",
        "carouselRadius",
        "dataRadius",
        "treeRadius",
        "tabRadius",
        "chipRadius",
        "pinRadius",
        "sliderTrackRadius",
        "beforeAfterRadius",
    ):
        assert window.property(property_name) == pytest.approx(0)
    for property_name in (
        "avatarBorderWidth",
        "badgeBorderWidth",
        "tagBorderWidth",
        "tabBorderWidth",
        "chipBorderWidth",
        "pinBorderWidth",
        "sliderHandleBorderWidth",
    ):
        assert window.property(property_name) == pytest.approx(1)
    assert warnings == []


def test_ticket_semantic_round_shapes_keep_their_geometry(ticket_controls):
    window, warnings = ticket_controls
    radio = _single(window, "ToggleRadioIndicator")
    switch = _single(window, "ToggleSwitchIndicator")

    assert window.property("avatarRadius") == pytest.approx(22)
    assert window.property("badgeRadius") * 2 == pytest.approx(
        window.findChild(QQuickItem, "ticketBadge").height()
    )
    assert radio.property("radius") * 2 == pytest.approx(radio.width())
    assert radio.property("_indicatorBorderWidth") == pytest.approx(1)
    assert switch.property("radius") * 2 == pytest.approx(switch.height())
    assert switch.property("_trackBorderWidth") == pytest.approx(1)
    handle = next(
        item
        for item in switch.childItems()
        if item.metaObject().indexOfProperty("radius") >= 0
        and item.metaObject().indexOfProperty("border") >= 0
    )
    assert handle.property("radius") * 2 == pytest.approx(handle.width())
    assert switch.property("_handleBorderWidth") == pytest.approx(1)
    assert warnings == []


def test_ticket_data_paper_is_visible_and_all_elevation_is_hidden(ticket_controls):
    window, warnings = ticket_controls
    papers = _objects(window, "TicketPaper")
    soft_shadows = _objects(window, "RectangularShadow")
    neo_shadows = _objects(window, "NeoShadow")

    assert len(papers) == 2
    assert all(bool(item.property("visible")) for item in papers)
    assert all(item.parent().property("radius") == pytest.approx(0) for item in papers)
    assert all(
        QQmlProperty(item.parent(), "border.width").read() == pytest.approx(1)
        for item in papers
    )
    assert soft_shadows
    assert all(not bool(item.property("visible")) for item in soft_shadows)
    assert neo_shadows
    assert all(not bool(item.property("visible")) for item in neo_shadows)
    assert warnings == []
