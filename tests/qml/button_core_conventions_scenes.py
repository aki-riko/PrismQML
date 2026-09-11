# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QML scene data strings used by button_core_conventions_shared."""

SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    id: root

    property int featureUnderTest: Enums.button.feature_none

    readonly property int featureNone: Enums.button.feature_none
    readonly property int featureDropdown: Enums.button.feature_dropdown
    readonly property int featureSplit: Enums.button.feature_split
    readonly property int featureProgress: Enums.button.feature_progress_bar
    readonly property int alignCenter: Enums.button.align_center
    readonly property int alignLeft: Enums.button.align_left
    readonly property int contentLeftMargin: Enums.spacing.m
    readonly property int menuContentLeadingPadding: Enums.spacing.l
    readonly property int menuContentTrailingPadding: Enums.spacing.xs
    readonly property int menuPaddingTolerance: Enums.spacing.xxs
    readonly property int buttonMinWidth: Enums.controlSize.buttonMinWidth
    readonly property int buttonHeight: Enums.controlSize.buttonHeight
    readonly property int splitArrowWidth: Enums.controlSize.splitButtonArrowWidth
    readonly property int wideMenuPadding: Enums.spacing.xxxl
    readonly property real aliasBorderWidth: aliasButton.border.width
    readonly property color aliasBorderColor: aliasButton.border.color
    readonly property real expectedBorderWidth: Enums.border.thick
    readonly property color expectedBorderColor: Enums.accentColor
    readonly property color expectedLifecycleBackground: lifecycleButton.color
    readonly property color expectedLifecycleBorder: lifecycleButton.styleHelper.borderColor
    readonly property color expectedLifecycleText: lifecycleButton.getTextColor()

    width: 500
    height: 220

    Button {
        id: aliasButton
        objectName: "aliasButton"
        width: 160
        height: 40
        text: "Alias"
        border.width: Enums.border.thick
        border.color: Enums.accentColor
    }

    Button {
        id: customButton
        objectName: "customButton"
        y: 50
        width: 160
        height: 40
        text: "Ignored default content"

        Rectangle {
            id: customPayload
            objectName: "customPayload"
            width: 37
            height: 19
            color: Enums.transparent
        }
    }

    Button {
        id: lifecycleButton
        objectName: "lifecycleButton"
        y: 100
        width: 180
        height: 40
        style: Enums.button.style_primary
        text: "State"
        icon: Enums.icon.checkmark
        feature: root.featureUnderTest
        menuItems: ["Alpha", "Beta"]
        progress: 0.4
        showProgress: true
        toolTipText: ""
    }

    MenuBar {
        id: menuBar
        objectName: "menuBar"
        x: 220
        width: 200
        itemPadding: root.wideMenuPadding
        items: ["File"]
    }

    Button {
        id: pillDropdownButton
        objectName: "pillDropdownButton"
        x: 220
        y: 50
        width: contentWidth
        height: contentHeight
        shape: Enums.button.shape_pill
        feature: Enums.button.feature_dropdown
        text: "DropDown"
        menuItems: ["Alpha", "Beta"]
    }

    Button {
        id: pillSplitButton
        objectName: "pillSplitButton"
        x: 220
        y: 100
        width: contentWidth
        height: contentHeight
        shape: Enums.button.shape_pill
        feature: Enums.button.feature_split
        text: "Split"
        menuItems: ["Alpha", "Beta"]
    }

    Button {
        id: compactSplitButton
        objectName: "compactSplitButton"
        x: 350
        y: 100
        width: contentWidth
        height: contentHeight
        shape: Enums.button.shape_pill
        feature: Enums.button.feature_split
        text: "I"
        menuItems: ["Alpha", "Beta"]
    }

    Button {
        id: gradientButtonA
        objectName: "gradientButtonA"
        x: 0
        y: 160
        style: Enums.button.style_gradient
        text: "Gradient A"
    }

    Button {
        id: gradientButtonB
        objectName: "gradientButtonB"
        x: 180
        y: 160
        style: Enums.button.style_gradient
        text: "Gradient B"
    }
}
"""
