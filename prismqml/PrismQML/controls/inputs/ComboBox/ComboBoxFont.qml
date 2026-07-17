// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import ".."
import "../../data/Label"
import QtQuick  // Keep after library imports so native types win 去前缀后保原生类型不被库覆盖

// ComboBoxFont - Font picker extending ComboBoxCore 字体选择框
ComboBoxCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var fonts: Enums.comboBox.fontFamilies.slice()
    property string currentFont: Enums.comboBox.fontDefaultFamily

    // ==================== Signals 信号 ====================
    signal fontSelected(string fontName)

    // Use fonts as model 使用fonts作为model
    model: fonts
    popupItemHeight: Enums.controlSize.calendarCellHeight

    // ==================== Content 内容 ====================
    popupDelegate: Component {
        Rectangle {
            id: fontItemBg
            property bool selected: modelData === control.currentFont

            width: ListView.view ? ListView.view.width : Enums.comboBox.fontDelegateFallbackWidth
            height: control.popupItemHeight
            radius: Enums.radius.small

            color: {
                if (fontItemArea.pressed) return Enums.stateColor.menuItemPressed
                if (selected) return Enums.stateColor.menuItemPressed
                if (fontItemArea.containsMouse) return Enums.stateColor.menuItemHover
                return Enums.transparent
            }

            // Selection indicator 选中指示器
            Rectangle {
                anchors.left: parent.left
                anchors.leftMargin: Enums.spacing.xxs
                anchors.verticalCenter: parent.verticalCenter
                width: Enums.controlSize.topNavIndicatorHeight
                height: Enums.spacing.xl
                radius: Enums.radius.micro
                color: Enums.accentColor
                visible: fontItemBg.selected
            }

            Label {
                type: Enums.label.type_body
                anchors.left: parent.left
                anchors.leftMargin: Enums.spacing.l
                anchors.verticalCenter: parent.verticalCenter
                text: modelData
                font.family: modelData
            }

            MouseArea {
                id: fontItemArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    control.currentFont = modelData
                    control.currentIndex = index
                    control.fontSelected(modelData)
                    control.closePopup()
                }
            }
        }
    }
}
