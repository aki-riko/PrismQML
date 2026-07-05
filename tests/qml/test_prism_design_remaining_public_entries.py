# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design remaining public entry skin tests."""

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, register_types, setSkin, setTheme


def _build(engine, qml: bytes):
    component = QQmlComponent(engine)
    component.setData(qml, QUrl("inline"))
    assert not component.isError(), [error.toString() for error in component.errors()]

    item = component.create(engine.rootContext())
    assert item is not None, [error.toString() for error in component.errors()]
    return component, item


def _rgb(qcolor):
    return (
        round(qcolor.redF() * 255),
        round(qcolor.greenF() * 255),
        round(qcolor.blueF() * 255),
    )


def _assert_common(item, accent, divider, header, card, border):
    expected_warning = (157, 93, 0) if accent == (22, 124, 128) else (192, 144, 0)

    assert item.property("focusRadius") == 4
    assert _rgb(item.property("focusColor")) == accent
    assert item.property("spinButtonRadius") == 4
    assert _rgb(item.property("separatorColor")) == divider
    assert _rgb(item.property("timelineInfoColor")) == accent
    assert _rgb(item.property("timelineCoreWarningColor")) == expected_warning
    assert item.property("waterfallColumns") == 2
    assert item.property("waterfallSpacing") == 12
    assert item.property("settingsImplicitHeight") > 0
    assert item.property("settingsContentImplicitWidth") > 0
    assert item.property("listRadius") == 6
    assert item.property("tableRadius") == 6
    assert item.property("treeRadius") == 6
    assert _rgb(item.property("listCardColor")) == card
    assert _rgb(item.property("tableHeaderColor")) == header
    assert _rgb(item.property("treeBorderColor")) == border


def test_prism_design_remaining_public_entries_light_and_dark(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build(engine, b"""
import QtQuick
import PrismQML
Item {
    width: 760
    height: 620

    property int focusRadius: focusLine.parentRadius
    property color focusColor: focusLine.lineColor
    property int spinButtonRadius: spinButton.radius
    property color separatorColor: separator.lineColor
    property color timelineInfoColor: timeline._getStatusColor("info")
    property color timelineCoreWarningColor: timelineCore._getStatusColor("warning")
    property int waterfallColumns: waterfall.columns
    property int waterfallSpacing: waterfall.spacing
    property int settingsImplicitHeight: settingsCard.implicitHeight
    property int settingsContentImplicitWidth: settingsContent.implicitWidth
    property int listRadius: listView.borderRadius
    property int tableRadius: tableView.borderRadius
    property int treeRadius: treeView.borderRadius
    property color listCardColor: listView.cardColor
    property color tableHeaderColor: tableView.headerColor
    property color treeBorderColor: treeView.borderColor

    Item {
        id: focusHost
        width: 180
        height: 32
        FocusLine {
            id: focusLine
            showLine: true
        }
    }

    SpinBoxButton {
        id: spinButton
        y: 40
        text: "+"
    }

    Separator {
        id: separator
        y: 80
        lineLength: 160
    }

    Timeline {
        id: timeline
        y: 110
        width: 320
        items: [
            { "title": "Plan", "status": "info", "cards": [{ "text": "Token evidence", "status": "success" }] }
        ]
    }

    TimelineCore {
        id: timelineCore
        x: 340
        y: 110
        width: 320
        items: [
            { "title": "Review", "status": "warning", "cards": ["Audit"] }
        ]
    }

    Waterfall {
        id: waterfall
        y: 260
        width: 220
        model: [32, 48]
        delegate: Rectangle {
            height: modelData
            color: Enums.cardColor
            radius: Enums.prismDesign.radiusCard
        }
    }

    SettingsCard {
        id: settingsCard
        x: 240
        y: 260
        width: 320
        title: "Sync"
        content: "Prism settings"
        type: Enums.settingCard.type_switch
        checked: true
    }

    SettingsCardContent {
        id: settingsContent
        x: 580
        y: 260
        type: Enums.settingCard.type_primary_push
        buttonText: "Run"
    }

    ListView {
        id: listView
        y: 360
        width: 180
        height: 120
        model: ["Alpha", "Beta"]
        delegate: Rectangle {
            width: ListView.view ? ListView.view.width : 120
            height: 28
            color: Enums.tableHoverColor
        }
    }

    TableView {
        id: tableView
        x: 200
        y: 360
        width: 240
        height: 120
        columns: [{ "text": "Name", "width": 0.5 }, { "text": "State", "fillWidth": true }]
        model: ["Alpha", "Beta"]
        delegate: Rectangle {
            width: TableView.view ? TableView.view.width : 160
            height: 28
            color: Enums.cardColor
        }
    }

    TreeView {
        id: treeView
        x: 460
        y: 360
        width: 240
        height: 120
        model: [
            { "text": "Root", "expanded": true, "children": [{ "text": "Leaf" }] }
        ]
    }
}
"""))
        light = keep[-1][1]
        qapp.processEvents()
        _assert_common(
            light,
            accent=(22, 124, 128),
            divider=(213, 223, 221),
            header=(230, 236, 235),
            card=(252, 254, 253),
            border=(221, 230, 228),
        )

        setTheme(Theme.DARK)
        keep.append(_build(engine, b"""
import QtQuick
import PrismQML
Item {
    width: 760
    height: 620

    property int focusRadius: focusLine.parentRadius
    property color focusColor: focusLine.lineColor
    property int spinButtonRadius: spinButton.radius
    property color separatorColor: separator.lineColor
    property color timelineInfoColor: timeline._getStatusColor("info")
    property color timelineCoreWarningColor: timelineCore._getStatusColor("warning")
    property int waterfallColumns: waterfall.columns
    property int waterfallSpacing: waterfall.spacing
    property int settingsImplicitHeight: settingsCard.implicitHeight
    property int settingsContentImplicitWidth: settingsContent.implicitWidth
    property int listRadius: listView.borderRadius
    property int tableRadius: tableView.borderRadius
    property int treeRadius: treeView.borderRadius
    property color listCardColor: listView.cardColor
    property color tableHeaderColor: tableView.headerColor
    property color treeBorderColor: treeView.borderColor

    Item {
        width: 180
        height: 32
        FocusLine {
            id: focusLine
            showLine: true
        }
    }

    SpinBoxButton {
        id: spinButton
        y: 40
        text: "+"
    }

    Separator {
        id: separator
        y: 80
        lineLength: 160
    }

    Timeline {
        id: timeline
        y: 110
        width: 320
        items: [
            { "title": "Plan", "status": "info", "cards": [{ "text": "Token evidence", "status": "success" }] }
        ]
    }

    TimelineCore {
        id: timelineCore
        x: 340
        y: 110
        width: 320
        items: [
            { "title": "Review", "status": "warning", "cards": ["Audit"] }
        ]
    }

    Waterfall {
        id: waterfall
        y: 260
        width: 220
        model: [32, 48]
        delegate: Rectangle {
            height: modelData
            color: Enums.cardColor
            radius: Enums.prismDesign.radiusCard
        }
    }

    SettingsCard {
        id: settingsCard
        x: 240
        y: 260
        width: 320
        title: "Sync"
        content: "Prism settings"
        type: Enums.settingCard.type_switch
        checked: true
    }

    SettingsCardContent {
        id: settingsContent
        x: 580
        y: 260
        type: Enums.settingCard.type_primary_push
        buttonText: "Run"
    }

    ListView {
        id: listView
        y: 360
        width: 180
        height: 120
        model: ["Alpha", "Beta"]
        delegate: Rectangle {
            width: ListView.view ? ListView.view.width : 120
            height: 28
            color: Enums.tableHoverColor
        }
    }

    TableView {
        id: tableView
        x: 200
        y: 360
        width: 240
        height: 120
        columns: [{ "text": "Name", "width": 0.5 }, { "text": "State", "fillWidth": true }]
        model: ["Alpha", "Beta"]
        delegate: Rectangle {
            width: TableView.view ? TableView.view.width : 160
            height: 28
            color: Enums.cardColor
        }
    }

    TreeView {
        id: treeView
        x: 460
        y: 360
        width: 240
        height: 120
        model: [
            { "text": "Root", "expanded": true, "children": [{ "text": "Leaf" }] }
        ]
    }
}
"""))
        dark = keep[-1][1]
        qapp.processEvents()
        _assert_common(
            dark,
            accent=(85, 214, 210),
            divider=(37, 52, 55),
            header=(16, 23, 25),
            card=(25, 34, 36),
            border=(34, 48, 51),
        )
    finally:
        for component, item in reversed(keep):
            item.deleteLater()
            component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        qapp.processEvents()
        setTheme(Theme.LIGHT)
        setSkin(Skin.FLUENT)
