# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design public alias and core entry skin tests."""

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


def _alpha(qcolor):
    return round(qcolor.alphaF() * 255)


def test_prism_design_public_aliases_light_and_dark(qapp):
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
    width: 480
    height: 360

    property int buttonRadius: buttonCore.radius
    property color buttonColor: buttonCore.color
    property int customRadius: customButton.radius_
    property color customColor: customButton.getBackgroundColor()
    property int buttonContentWidth: buttonContent.implicitWidth
    property color buttonContentRing: buttonContent._ringColor
    property color buttonProgressColor: buttonProgress._progressColor
    property color buttonProgressTrack: buttonProgress._trackColor
    property int lineRadius: lineEdit.radius
    property color lineColor: lineEdit.color
    property string lineText: lineEdit.text
    property int comboEntryHeight: comboEntry.implicitHeight
    property string comboEntryText: comboEntry.currentText
    property int comboDefaultRadius: comboDefault.radius
    property string comboDefaultText: comboDefault.currentText
    property int sliderBorderWidth: sliderCore._handleBorderWidth
    property color sliderTrackColor: sliderCore._trackColor
    property color ratingOutlineColor: ratingCore._effectiveOutlineColor
    property color calendarRangeColor: calendarCore._rangeBarColor

    ButtonCore {
        id: buttonCore
        text: "Run"
        style: Enums.button.style_primary
    }

    CustomButtonCore {
        id: customButton
        text: "Legacy"
    }

    ButtonContent {
        id: buttonContent
        feature: Enums.button.feature_progress_ring
        style: Enums.button.style_primary
        text: "Loading"
        icon: ""
        iconSize: Enums.iconSize.m
        loading: false
        loadingText: ""
        progress: 0.5
        textColor: Enums.accentForeground
        controlEnabled: true
        fontFamily: Enums.fontFamily
        fontSize: Enums.typography.body
        pressed: false
    }

    ButtonProgress {
        id: buttonProgress
        width: 120
        feature: Enums.button.feature_progress_bar
        style: Enums.button.style_primary
        progress: 0.5
        showProgress: true
        parentRadius: Enums.prismDesign.radiusControl
    }

    LineEdit {
        id: lineEdit
        text: "Prism"
        placeholderText: "Name"
    }

    ComboBoxEntry {
        id: comboEntry
        model: ["Alpha", "Beta"]
        currentIndex: 1
    }

    ComboBoxDefault {
        id: comboDefault
        model: ["One", "Two"]
        currentIndex: 1
    }

    SliderCore {
        id: sliderCore
        value: 42
    }

    RatingCore {
        id: ratingCore
        value: 3
    }

    CalendarPickerCore {
        id: calendarCore
        year: 2026
        month: 7
        day: 5
        rangeMode: true
        rangeStart: new Date(2026, 6, 3)
        rangeEnd: new Date(2026, 6, 8)
    }
}
"""))
        controls = keep[-1][1]
        qapp.processEvents()
        assert controls.property("buttonRadius") == 6
        assert _rgb(controls.property("buttonColor")) == (47, 111, 237)
        assert controls.property("customRadius") == 6
        assert _rgb(controls.property("customColor")) == (255, 255, 255)
        assert controls.property("buttonContentWidth") > 0
        assert _rgb(controls.property("buttonContentRing")) == (255, 255, 255)
        assert _rgb(controls.property("buttonProgressColor")) == (255, 255, 255)
        assert _alpha(controls.property("buttonProgressTrack")) == 77
        assert controls.property("lineRadius") == 6
        assert _rgb(controls.property("lineColor")) == (255, 255, 255)
        assert controls.property("lineText") == "Prism"
        assert controls.property("comboEntryHeight") == 32
        assert controls.property("comboEntryText") == "Beta"
        assert controls.property("comboDefaultRadius") == 6
        assert controls.property("comboDefaultText") == "Two"
        assert controls.property("sliderBorderWidth") == 1
        assert _rgb(controls.property("sliderTrackColor")) == (234, 241, 247)
        assert _rgb(controls.property("ratingOutlineColor")) == (131, 146, 164)
        assert _rgb(controls.property("calendarRangeColor")) == (240, 240, 240)

        keep.append(_build(engine, b"""
import QtQuick
import PrismQML
Item {
    width: 640
    height: 420

    property int tooltipCoreRadius: tooltipCore._tooltipRadius
    property color tooltipCoreBackground: tooltipCore._tooltipBackground
    property color tooltipCoreBorder: tooltipCore._tooltipBorderColor
    property int toolTipRadius: toolTip._tooltipRadius
    property int infoRadius: infoBar._infoBarRadius
    property color infoBackground: infoBar._infoBarBackground
    property color infoBorder: infoBar._infoBarBorderColor
    property color progressColor: progress.progressColor
    property color progressTrack: progress.trackColor
    property int expanderRadius: expander._radius
    property int settingsSpacing: settingsGroup.spacing
    property int breadcrumbCount: breadcrumb.count
    property string breadcrumbKey: breadcrumb.currentKey
    property int stackedCount: stacked.count
    property int menuHeight: menuBar.implicitHeight
    property int scrollPadding: scrollArea.padding
    property int componentSpacing: componentCard.spacing
    property int exampleWidth: exampleCard.implicitWidth

    TooltipCore {
        id: tooltipCore
        text: "Tooltip"
    }

    ToolTip {
        id: toolTip
        text: "Alias"
    }

    InfoBarCore {
        id: infoBar
        title: "Core"
        message: "Direct info"
        severity: "info"
        duration: 0
    }

    ProgressCore {
        id: progress
        value: 50
    }

    ExpanderCore {
        id: expander
        title: "Section"
        content: "Details"
    }

    SettingsCardGroup {
        id: settingsGroup
        title: "Settings"
    }

    Breadcrumb {
        id: breadcrumb
        Component.onCompleted: {
            addItem("home", "Home", "Home")
            addItem("settings", "Settings", "Settings")
        }
    }

    StackedWidget {
        id: stacked
        width: 240
        height: 120
        currentIndex: 1
        Rectangle { color: Enums.surfaceColor }
        Rectangle { color: Enums.cardColor }
    }

    MenuBar {
        id: menuBar
        items: [{ "text": "File", "children": [{ "text": "Open" }] }]
    }

    ScrollArea {
        id: scrollArea
        preferredWidth: 160
        preferredHeight: 100
        Rectangle {
            width: 220
            height: 160
            color: Enums.cardColor
        }
    }

    ComponentCard {
        id: componentCard
        label: "Prism"
        Button { text: "Child" }
    }

    ExampleCard {
        id: exampleCard
        title: "Example"
        description: "Description"
        componentName: "Button"
        Button { text: "OK" }
    }
}
"""))
        structure = keep[-1][1]
        qapp.processEvents()
        assert structure.property("tooltipCoreRadius") == 10
        assert _rgb(structure.property("tooltipCoreBackground")) == (248, 251, 255)
        assert _rgb(structure.property("tooltipCoreBorder")) == (217, 227, 236)
        assert structure.property("toolTipRadius") == 10
        assert structure.property("infoRadius") == 10
        assert _rgb(structure.property("infoBackground")) == (204, 228, 247)
        assert _rgb(structure.property("infoBorder")) == (217, 227, 236)
        assert _rgb(structure.property("progressColor")) == (47, 111, 237)
        assert _rgb(structure.property("progressTrack")) == (234, 241, 247)
        assert structure.property("expanderRadius") == 8
        assert structure.property("settingsSpacing") == 2
        assert structure.property("breadcrumbCount") == 2
        assert structure.property("breadcrumbKey") == "settings"
        assert structure.property("stackedCount") == 2
        assert structure.property("menuHeight") == 32
        assert structure.property("scrollPadding") == 16
        assert structure.property("componentSpacing") == 4
        assert structure.property("exampleWidth") == 600

        keep.append(_build(engine, b"""
import QtQuick
import PrismQML
Item {
    width: 420
    height: 240

    property int flowCount: flow.itemCount
    property int hboxCount: hbox.count()
    property int vboxCount: vbox.count()
    property int gridCount: grid.count()
    property real rowScale: rowFitScaleProbe.scale

    FlowLayout {
        id: flow
        width: 180
        Rectangle { width: 70; height: 20; color: Enums.cardColor }
        Rectangle { width: 70; height: 20; color: Enums.cardColor }
    }

    HBoxLayout {
        id: hbox
        y: 40
        width: 180
        Rectangle { width: 40; height: 20; color: Enums.cardColor }
        Rectangle { width: 40; height: 20; color: Enums.cardColor }
    }

    VBoxLayout {
        id: vbox
        y: 80
        width: 180
        Rectangle { width: 40; height: 20; color: Enums.cardColor }
        Rectangle { width: 40; height: 20; color: Enums.cardColor }
    }

    GridLayout {
        id: grid
        y: 130
        width: 180
        columns: 2
        Rectangle { width: 40; height: 20; color: Enums.cardColor }
        Rectangle { width: 40; height: 20; color: Enums.cardColor }
    }

    RowFit {
        id: rowFit
        y: 180
        width: 80
        autoFit: true
        Rectangle {
            id: rowFitScaleProbe
            width: 120
            height: 20
            color: Enums.cardColor
        }
    }
}
"""))
        layout = keep[-1][1]
        qapp.processEvents()
        assert layout.property("flowCount") == 2
        assert layout.property("hboxCount") == 2
        assert layout.property("vboxCount") == 2
        assert layout.property("gridCount") == 2
        assert round(layout.property("rowScale"), 2) <= 1.0

        setTheme(Theme.DARK)
        keep.append(_build(engine, b"""
import QtQuick
import PrismQML
Item {
    property int buttonRadius: buttonCore.radius
    property int customRadius: customButton.radius_
    property color lineColor: lineEdit.color
    property color lineTextColor: lineEdit.inputTextColor
    property color tooltipBackground: tooltip._tooltipBackground
    property color tooltipBorder: tooltip._tooltipBorderColor
    property color progressTrack: progress.trackColor
    property color ratingOutlineColor: rating._effectiveOutlineColor
    property color calendarRangeColor: calendar._rangeBarColor

    ButtonCore {
        id: buttonCore
        text: "Run"
        style: Enums.button.style_primary
    }

    CustomButtonCore {
        id: customButton
        text: "Legacy"
    }

    LineEdit {
        id: lineEdit
        text: "Prism"
    }

    TooltipCore {
        id: tooltip
        text: "Dark"
    }

    ProgressCore {
        id: progress
        value: 50
    }

    RatingCore {
        id: rating
        value: 3
    }

    CalendarPickerCore {
        id: calendar
        year: 2026
        month: 7
        rangeMode: true
        rangeStart: new Date(2026, 6, 3)
        rangeEnd: new Date(2026, 6, 8)
    }
}
"""))
        dark_controls = keep[-1][1]
        assert dark_controls.property("buttonRadius") == 6
        assert dark_controls.property("customRadius") == 6
        assert _rgb(dark_controls.property("lineColor")) == (32, 38, 46)
        assert _rgb(dark_controls.property("lineTextColor")) == (238, 243, 248)
        assert _rgb(dark_controls.property("tooltipBackground")) == (36, 43, 52)
        assert _rgb(dark_controls.property("tooltipBorder")) == (48, 58, 70)
        assert _rgb(dark_controls.property("progressTrack")) == (21, 26, 32)
        assert _rgb(dark_controls.property("ratingOutlineColor")) == (118, 131, 148)
        assert _rgb(dark_controls.property("calendarRangeColor")) == (38, 38, 38)
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
