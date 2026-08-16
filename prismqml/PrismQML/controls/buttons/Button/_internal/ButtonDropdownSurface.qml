// ButtonDropdownSurface - Split and dropdown button surface 分离与下拉按钮表面
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../containers/Separator"
import "../../../icons"

// ButtonDropdownSurface - Owns split/dropdown hit targets and arrow 承载分离/下拉命中区与箭头
Item {
    id: surface

    // ==================== Required Props 必需属性 ====================
    required property var dropdownControl

    // ==================== Readonly State 只读状态 ====================
    readonly property bool mainHovered: splitMainMouse.containsMouse
    readonly property bool mainPressed: splitMainMouse.pressed
    readonly property bool dropHovered: splitDropMouse.containsMouse
    readonly property bool dropPressed: splitDropMouse.pressed

    anchors.fill: parent

    // ==================== Content 内容 ====================
    // Split main button hover area 分离按钮主悬浮区域
    Rectangle {
        id: splitMainArea

        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.right: splitLine.left
        anchors.margins: Enums.spacing.micro
        radius: Math.max(Enums.radius.none,
                         surface.dropdownControl.parentRadius - 1)
        color: splitMainMouse.pressed
               ? surface.dropdownControl._splitPressedColor
               : (splitMainMouse.containsMouse
                  ? surface.dropdownControl._splitHoverColor
                  : surface.dropdownControl._splitTransparent)
        visible: surface.dropdownControl.feature === Enums.button.feature_split

        HoverBehavior on color {
            active: splitMainMouse.containsMouse && !splitMainMouse.pressed
            enterDuration: surface.dropdownControl._animationDuration
        }
    }

    // Split separator line 分离线
    Separator {
        id: splitLine

        type: Enums.separator.vertical
        anchors.right: splitDropArea.left
        anchors.verticalCenter: parent.verticalCenter
        lineLength: parent.height - Enums.spacing.l
        lineColor: surface.dropdownControl._separatorColor
        visible: surface.dropdownControl.feature === Enums.button.feature_split
    }

    // Split dropdown area 分离按钮下拉区域
    Rectangle {
        id: splitDropArea

        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.margins: Enums.spacing.micro
        width: Enums.spacing.xxxl
        radius: Math.max(Enums.radius.none,
                         surface.dropdownControl.parentRadius - 1)
        color: splitDropMouse.pressed
               ? surface.dropdownControl._splitPressedColor
               : (splitDropMouse.containsMouse
                  ? surface.dropdownControl._splitHoverColor
                  : surface.dropdownControl._splitTransparent)
        visible: surface.dropdownControl.feature === Enums.button.feature_split

        HoverBehavior on color {
            active: splitDropMouse.containsMouse && !splitDropMouse.pressed
            enterDuration: surface.dropdownControl._animationDuration
        }

        MouseArea {
            id: splitDropMouse

            anchors.fill: parent
            hoverEnabled: true
            enabled: surface.dropdownControl.controlEnabled
                      && !surface.dropdownControl.loading
            cursorShape: enabled
                         && surface.dropdownControl.parentStyle
                            === Enums.button.style_hyperlink
                         ? Qt.PointingHandCursor : Qt.ArrowCursor
            onContainsMouseChanged: {
                if (splitDropMouse.containsMouse)
                    surface.dropdownControl.prewarmMenu()
            }
            onClicked: surface.dropdownControl.openMenu()
        }
    }

    // Shared dropdown/split arrow 复用的下拉/分离箭头
    ChevronIcon {
        id: menuArrow

        anchors.centerIn: surface.dropdownControl.feature
                          === Enums.button.feature_split
                          ? splitDropArea : undefined
        anchors.right: surface.dropdownControl.feature
                       === Enums.button.feature_dropdown
                       ? parent.right : undefined
        anchors.rightMargin: surface.dropdownControl.feature
                             === Enums.button.feature_dropdown
                             ? Enums.spacing.m : 0
        anchors.verticalCenter: surface.dropdownControl.feature
                                === Enums.button.feature_dropdown
                                ? parent.verticalCenter : undefined
        animated: true
        isOpen: (surface.dropdownControl.feature
                 === Enums.button.feature_dropdown
                 && surface.dropdownControl.dropdownOpen)
                || surface.dropdownControl.isMenuOpen
        color: surface.dropdownControl._arrowColor
        visible: surface.dropdownControl.feature === Enums.button.feature_split
                 || (surface.dropdownControl.feature
                     === Enums.button.feature_dropdown
                     && surface.dropdownControl.showDropdownIndicator)
    }

    // Split main button interaction 分离按钮主交互
    MouseArea {
        id: splitMainMouse

        anchors.fill: splitMainArea
        hoverEnabled: true
        enabled: surface.dropdownControl.controlEnabled
                  && !surface.dropdownControl.loading
                  && surface.dropdownControl.feature
                     === Enums.button.feature_split
        visible: surface.dropdownControl.feature === Enums.button.feature_split
        cursorShape: enabled
                     && surface.dropdownControl.parentStyle
                        === Enums.button.style_hyperlink
                     ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: surface.dropdownControl.mainButtonClicked()
    }
}
