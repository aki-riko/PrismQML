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
    // Construction may evaluate child bindings before ButtonDropdown assigns
    // its scope context. Start from global Enums, then accept the explicit
    // context binding without producing a transient warning.
    // 创建期可能先于 ButtonDropdown 注入范围上下文就求值子绑定。先回退全局 Enums，
    // 随后再接收显式上下文绑定，避免瞬时空值警告。
    property var skinContext: Enums
    readonly property var _skin: skinContext || Enums

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
        anchors.margins: surface._skin.spacing.micro
        radius: Math.max(surface._skin.radius.none,
                         surface.dropdownControl.parentRadius - 1)
        color: splitMainMouse.pressed
               ? surface.dropdownControl._splitPressedColor
               : (splitMainMouse.containsMouse
                  ? surface.dropdownControl._splitHoverColor
                  : surface.dropdownControl._splitTransparent)
        visible: surface.dropdownControl.feature === surface._skin.button.feature_split

        HoverBehavior on color {
            active: splitMainMouse.containsMouse && !splitMainMouse.pressed
            enterDuration: surface.dropdownControl._animationDuration
        }
    }

    // Split separator line 分离线
    Separator {
        id: splitLine

        skinContext: surface._skin
        type: surface._skin.separator.vertical
        anchors.right: splitDropArea.left
        anchors.verticalCenter: parent.verticalCenter
        lineLength: parent.height - surface._skin.spacing.l
        lineColor: surface.dropdownControl._separatorColor
        visible: surface.dropdownControl.feature === surface._skin.button.feature_split
    }

    // Split dropdown area 分离按钮下拉区域
    Rectangle {
        id: splitDropArea

        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.margins: surface._skin.spacing.micro
        width: surface._skin.spacing.xxxl
        radius: Math.max(surface._skin.radius.none,
                         surface.dropdownControl.parentRadius - 1)
        color: splitDropMouse.pressed
               ? surface.dropdownControl._splitPressedColor
               : (splitDropMouse.containsMouse
                  ? surface.dropdownControl._splitHoverColor
                  : surface.dropdownControl._splitTransparent)
        visible: surface.dropdownControl.feature === surface._skin.button.feature_split

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
                            === surface._skin.button.style_hyperlink
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
                          === surface._skin.button.feature_split
                          ? splitDropArea : undefined
        anchors.right: surface.dropdownControl.feature
                       === surface._skin.button.feature_dropdown
                       ? parent.right : undefined
        anchors.rightMargin: surface.dropdownControl.feature
                             === surface._skin.button.feature_dropdown
                             ? surface._skin.spacing.m : 0
        anchors.verticalCenter: surface.dropdownControl.feature
                                === surface._skin.button.feature_dropdown
                                ? parent.verticalCenter : undefined
        animated: true
        isOpen: (surface.dropdownControl.feature
                 === surface._skin.button.feature_dropdown
                 && surface.dropdownControl.dropdownOpen)
                || surface.dropdownControl.isMenuOpen
        color: surface.dropdownControl._arrowColor
        visible: surface.dropdownControl.feature === surface._skin.button.feature_split
                 || (surface.dropdownControl.feature
                     === surface._skin.button.feature_dropdown
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
                     === surface._skin.button.feature_split
        visible: surface.dropdownControl.feature === surface._skin.button.feature_split
        cursorShape: enabled
                     && surface.dropdownControl.parentStyle
                        === surface._skin.button.style_hyperlink
                     ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: surface.dropdownControl.mainButtonClicked()
    }
}
