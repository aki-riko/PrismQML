# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Vintage ticket container and feedback regressions. 复古票据容器与反馈回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickWindow

from prismqml import Skin, getSkin, register_types, setSkin


ROOT = Path(__file__).resolve().parents[2]
QML_ROOT = ROOT / "prismqml" / "PrismQML"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "vintage-ticket-extended-surfaces.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    readonly property real drawerRadius: drawer._effectiveRadius
    readonly property real drawerBorderWidth: drawer._drawerBorderWidth
    readonly property real expanderRadius: expander._radius
    readonly property real groupRadius: groupBox._borderRadius
    readonly property real maskedRadius: masked._dialogRadius
    readonly property real maskedBorderWidth: masked._dialogBorderWidth
    readonly property real infoRadius: infoBar._infoBarRadius
    readonly property real infoBorderWidth: infoBar._infoBarBorderWidth
    readonly property real toastRadius: toast._toastRadius
    readonly property real toastBorderWidth: toast._toastBorderWidth
    readonly property real bubbleRadius: bubble._bubbleRadius
    readonly property real bubbleBorderWidth: bubble._bubbleBorderWidth
    readonly property real tooltipRadius: tooltip._tooltipRadius
    readonly property real tooltipBorderWidth: tooltip._tooltipBorderWidth

    function openTicketSurfaces() {
        drawer.open()
        masked.open()
    }

    width: 960
    height: 720
    visible: true
    color: Enums.backgroundColor

    TicketPaper {
        anchors.fill: parent
    }

    Drawer {
        id: drawer
        objectName: "ticketDrawer"
        width: parent.width
        height: parent.height
        drawerWidth: 240
        radius: Enums.radius.large
        modal: false
    }

    Expander {
        id: expander
        objectName: "ticketExpander"
        x: 280
        y: 20
        width: 300
        title: "JOURNEY DETAILS"
        expanded: true

        Rectangle {
            width: 120
            height: 36
            color: Enums.transparent
        }
    }

    GroupBox {
        id: groupBox
        objectName: "ticketGroupBox"
        x: 620
        y: 20
        width: 280
        height: 140
        title: "PASSENGER"
    }

    MaskedDialog {
        id: masked
        objectName: "ticketMaskedDialog"
        overlayTarget: root.contentItem
        body.width: 320
        body.height: 180
    }

    InfoBarCore {
        id: infoBar
        objectName: "ticketInfoBar"
        x: 280
        y: 220
        width: 300
        severity: "success"
        title: "VALIDATED"
        message: "Gate 04"
        desktopMode: true
    }

    Toast {
        id: toast
        objectName: "ticketToast"
        x: 620
        y: 220
        width: 280
        severity: "warning"
        title: "LAST CALL"
        message: "Platform 2"
        desktopMode: true
        duration: 0
    }

    ChatBubble {
        id: bubble
        objectName: "ticketBubble"
        x: 280
        y: 350
        width: 300
        role: "assistant"
        content: "Ticket confirmed"
        showAvatar: false
    }

    TooltipCore {
        id: tooltip
        objectName: "ticketTooltip"
        text: "Serial number"
    }

    ProgressBar {
        id: progressBar
        objectName: "ticketProgress"
        x: 620
        y: 380
        width: 280
        value: 62
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
    assert QMetaObject.invokeMethod(window, "openTicketSurfaces")
    _pump(350)
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


def _owned(root: QObject, type_fragment: str) -> list[QObject]:
    return [
        child
        for child in root.findChildren(QObject)
        if type_fragment in child.metaObject().className()
    ]


@pytest.fixture
def ticket_scene(qapp):
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


def test_ticket_extended_surfaces_use_square_ink_geometry(ticket_scene):
    window, warnings = ticket_scene
    for property_name in (
        "drawerRadius",
        "expanderRadius",
        "groupRadius",
        "maskedRadius",
        "infoRadius",
        "toastRadius",
        "bubbleRadius",
        "tooltipRadius",
    ):
        assert window.property(property_name) == pytest.approx(0)
    for property_name in (
        "drawerBorderWidth",
        "maskedBorderWidth",
        "infoBorderWidth",
        "toastBorderWidth",
        "bubbleBorderWidth",
        "tooltipBorderWidth",
    ):
        assert window.property(property_name) == pytest.approx(1)
    assert warnings == []


def test_ticket_large_surfaces_use_paper_and_all_elevation_is_hidden(ticket_scene):
    window, warnings = ticket_scene
    papers = _owned(window, "TicketPaper")
    soft_shadows = _owned(window, "RectangularShadow")
    neo_shadows = _owned(window, "NeoShadow")

    assert len(papers) >= 3
    assert all(bool(item.property("visible")) for item in papers)
    assert all(not bool(item.property("visible")) for item in soft_shadows)
    assert all(not bool(item.property("visible")) for item in neo_shadows)
    assert warnings == []


def test_ticket_group_box_preserves_parent_paper_through_title_gap(ticket_scene):
    window, warnings = ticket_scene
    group_box = window.findChild(QObject, "ticketGroupBox")
    standard_border = group_box.findChild(QObject, "groupBoxStandardBorder")
    ticket_border = group_box.findChild(QObject, "groupBoxTicketBorder")
    title_background = group_box.findChild(QObject, "groupBoxTitleBackground")
    top_left = group_box.findChild(QObject, "groupBoxTicketTopLeft")
    top_right = group_box.findChild(QObject, "groupBoxTicketTopRight")

    assert all(
        item is not None
        for item in (
            standard_border,
            ticket_border,
            title_background,
            top_left,
            top_right,
        )
    )
    assert not bool(standard_border.property("visible"))
    assert bool(ticket_border.property("visible"))
    assert not bool(title_background.property("visible"))
    assert top_left.property("width") > 0
    assert top_right.property("width") > 0
    assert top_left.property("x") + top_left.property("width") == pytest.approx(
        title_background.property("x")
    )
    assert top_right.property("x") == pytest.approx(
        title_background.property("x") + title_background.property("width")
    )
    assert warnings == []


def test_ticket_feedback_keeps_lightweight_notification_contracts():
    info_source = (
        QML_ROOT / "controls" / "feedback" / "InfoBar" / "InfoBarCore.qml"
    ).read_text(encoding="utf-8")
    toast_source = (
        QML_ROOT / "controls" / "feedback" / "Notification" / "Toast.qml"
    ).read_text(encoding="utf-8")
    progress_source = (
        QML_ROOT / "controls" / "feedback" / "Progress" / "ProgressBar.qml"
    ).read_text(encoding="utf-8")

    assert "TicketPaper" not in info_source
    assert "TicketPaper" not in toast_source
    assert "radius: Enums.isVintageTicket ? Enums.ticket.radius : height / 2" in progress_source
    assert "Enums.hasOutlinedSurfaces ? Enums.surfaceBorderWidth" in progress_source
